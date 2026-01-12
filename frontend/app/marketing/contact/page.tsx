export default function Contact() {
  return (
    <div className="bg-slate-950 text-white min-h-screen p-20">
      <h1 className="text-5xl font-extrabold">Talk with T79AI</h1>
      <p className="text-lg text-slate-300 mt-4 max-w-2xl">
        Tell us about your environment and security objectives. We’ll assemble a tailored pilot that
        integrates with your cloud, CI/CD, and identity stack.
      </p>

      <div className="mt-8 max-w-xl">
        <form className="space-y-6">
          <div>
            <label className="block text-sm font-semibold">Work Email</label>
            <input
              type="email"
              className="mt-2 w-full rounded-lg border border-slate-700 bg-slate-900 p-3 focus:border-blue-500 focus:outline-none"
              placeholder="you@company.com"
              required
            />
          </div>
          <div>
            <label className="block text-sm font-semibold">Company</label>
            <input
              type="text"
              className="mt-2 w-full rounded-lg border border-slate-700 bg-slate-900 p-3 focus:border-blue-500 focus:outline-none"
              placeholder="Your organization"
              required
            />
          </div>
          <div>
            <label className="block text-sm font-semibold">What do you want to secure?</label>
            <textarea
              className="mt-2 w-full rounded-lg border border-slate-700 bg-slate-900 p-3 focus:border-blue-500 focus:outline-none"
              rows={4}
              placeholder="Cloud footprint, CI/CD, Kubernetes, data stores, or all of the above"
            />
          </div>
          <button
            type="submit"
            className="w-full bg-blue-600 hover:bg-blue-700 py-3 rounded-lg font-semibold"
          >
            Request a demo
          </button>
        </form>
      </div>
    <div className="bg-slate-950 min-h-screen text-white px-20 py-20 grid grid-cols-1 md:grid-cols-2 gap-12 items-start">
      <div>
        <h1 className="text-6xl font-bold">Contact</h1>
        <p className="mt-6 text-xl text-slate-300 max-w-2xl">
          Talk with our security engineers about deployment, compliance, and custom integrations.
          We respond within one business day.
        </p>
        <div className="mt-10 space-y-4 text-slate-300">
          <p><strong className="text-white">Email:</strong> enterprise@t79.ai</p>
          <p><strong className="text-white">Phone:</strong> +1 (415) 555-0123</p>
          <p><strong className="text-white">Office:</strong> 500 Market St, Suite 2100, San Francisco, CA</p>
        </div>
      </div>

      <form className="bg-slate-900 p-8 rounded-2xl border border-slate-800 space-y-6">
        <div>
          <label className="block text-slate-400 mb-2" htmlFor="name">
            Name
          </label>
          <input
            id="name"
            type="text"
            className="w-full bg-slate-950 border border-slate-700 rounded-lg p-3 focus:outline-none focus:border-blue-500 text-white"
            placeholder="Your full name"
          />
        </div>
        <div>
          <label className="block text-slate-400 mb-2" htmlFor="email">
            Work email
          </label>
          <input
            id="email"
            type="email"
            className="w-full bg-slate-950 border border-slate-700 rounded-lg p-3 focus:outline-none focus:border-blue-500 text-white"
            placeholder="you@company.com"
          />
        </div>
        <div>
          <label className="block text-slate-400 mb-2" htmlFor="message">
            How can we help?
          </label>
          <textarea
            id="message"
            className="w-full bg-slate-950 border border-slate-700 rounded-lg p-3 h-32 focus:outline-none focus:border-blue-500 text-white"
            placeholder="Describe your use case or deployment needs"
          />
        </div>
        <button
          type="submit"
          className="w-full bg-blue-600 hover:bg-blue-700 py-3 rounded-lg font-semibold text-lg text-white transition"
        >
          Submit request
        </button>
      </form>
    </div>
  );
}
