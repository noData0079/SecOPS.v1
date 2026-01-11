export default function Contact() {
  return (
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
