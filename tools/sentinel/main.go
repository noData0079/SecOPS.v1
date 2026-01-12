package main

import (
	"crypto/ed25519"
	"crypto/tls"
	"crypto/x509"
	"encoding/hex"
	"flag"
	"fmt"
	"io"
	"log"
	"net/http"
	"os"
)

type SignedInstruction struct {
	Payload   string `json:"payload"`   // e.g., "patch --service=db"
	Signature string `json:"signature"` // Hex-encoded Ed25519 signature
}

func main() {
	// Flags for configuration
	certFile := flag.String("cert", "sentinel.crt", "Path to Sentinel certificate")
	keyFile := flag.String("key", "sentinel.key", "Path to Sentinel private key")
	caFile := flag.String("ca", "ca.crt", "Path to CA certificate")
	port := flag.String("port", "8443", "Port to listen on")
	flag.Parse()

	// Load Brain Public Key from Env
	brainKeyHex := os.Getenv("BRAIN_PUBLIC_KEY")
	if brainKeyHex == "" {
		log.Fatal("BRAIN_PUBLIC_KEY environment variable is required")
	}

	// 1. Setup mTLS (Mutual TLS)
	caCert, err := os.ReadFile(*caFile)
	if err != nil {
		log.Fatalf("Failed to read CA cert from %s: %v", *caFile, err)
	}
	caCertPool := x509.NewCertPool()
	if !caCertPool.AppendCertsFromPEM(caCert) {
		log.Fatal("Failed to append CA cert")
	}

	cert, err := tls.LoadX509KeyPair(*certFile, *keyFile)
	if err != nil {
		log.Fatalf("Failed to load Sentinel keypair from %s, %s: %v", *certFile, *keyFile, err)
	}

	tlsConfig := &tls.Config{
		Certificates: []tls.Certificate{cert},
		ClientCAs:    caCertPool,
		ClientAuth:   tls.RequireAndVerifyClientCert,
		MinVersion:   tls.VersionTLS13,
	}

	// 2. The Execution Handler
	http.HandleFunc("/execute", func(w http.ResponseWriter, r *http.Request) {
		if r.Method != http.MethodPost {
			http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
			return
		}

		body, _ := io.ReadAll(r.Body)

		// Expecting raw bytes where the first 128 chars are hex signature
		if len(body) < 129 {
			http.Error(w, "Invalid Payload", http.StatusBadRequest)
			return
		}

		sigHex := string(body[:128])
		msg := body[128:]

		sig, err := hex.DecodeString(sigHex)
        if err != nil {
            http.Error(w, "Invalid Signature Hex", http.StatusBadRequest)
            return
        }
		pubKey, err := hex.DecodeString(brainKeyHex)
		if err != nil {
			log.Printf("Invalid Brain Public Key: %v", err)
			http.Error(w, "Internal Server Error", http.StatusInternalServerError)
			return
		}

		if ed25519.Verify(pubKey, msg, sig) {
			fmt.Printf("[TRUSTED] Signature Valid. Executing: %s\n", string(msg))
			w.WriteHeader(http.StatusOK)
			w.Write([]byte("Action executed successfully"))
		} else {
			fmt.Println("[ALERT] INVALID SIGNATURE DETECTED. Blocking Execution.")
			http.Error(w, "Unauthorized: Signature Mismatch", http.StatusUnauthorized)
		}
	})

	addr := fmt.Sprintf(":%s", *port)
	server := &http.Server{
		Addr:      addr,
		TLSConfig: tlsConfig,
	}

	fmt.Printf("🛡️ Sovereign Mechanica Sentinel active on %s (mTLS secured)\n", addr)
	log.Fatal(server.ListenAndServeTLS("", ""))
}
