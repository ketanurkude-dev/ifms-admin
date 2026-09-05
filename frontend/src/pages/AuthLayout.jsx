// Shared two-column layout for the login and OTP screens:
// a branded left panel, and the form on the right.
export default function AuthLayout({ title, subtitle, children }) {
  return (
    <div className="h-screen flex bg-slate-50 overflow-hidden">
      <div className="hidden lg:flex lg:w-1/2 h-full relative flex-col justify-between bg-slate-900 p-12 text-white border-r border-slate-950">
        <div className="absolute top-0 left-0 w-full h-1.5 bg-amber-500" />

        <div>
          <div className="flex items-center gap-3 mb-1">
            <div className="w-9 h-9 rounded bg-white/10 border border-white/20 flex items-center justify-center text-sm font-semibold">
              AP
            </div>
            <span className="text-base font-semibold tracking-wide">Admin Portal</span>
          </div>
          <p className="text-slate-300 text-sm ml-[48px]">Integrated Financial Management System</p>
        </div>

        <div className="max-w-sm">
          <h2 className="text-2xl font-semibold leading-snug mb-4">
            One back office for every portal's pending requests
          </h2>
          <p className="text-slate-300 text-sm leading-relaxed">
            Review and decide requests raised on the Employee, Pensioner and Vendor portals from a single
            queue, based on your assigned permissions.
          </p>
        </div>

        <p className="text-xs text-slate-400">&copy; {new Date().getFullYear()} Admin Portal. For authorised use only.</p>
      </div>

      <div className="w-full lg:w-1/2 h-full overflow-y-auto flex items-center justify-center p-6 sm:p-10">
        <div className="w-full max-w-md">
          <div className="lg:hidden flex items-center gap-2 mb-8">
            <div className="w-8 h-8 rounded-full bg-slate-900 text-white flex items-center justify-center text-sm font-semibold">
              AP
            </div>
            <span className="font-semibold text-slate-800">Admin Portal</span>
          </div>

          <h1 className="text-2xl font-semibold text-slate-800 mb-1">{title}</h1>
          {subtitle && <p className="text-sm text-slate-500 mb-8">{subtitle}</p>}

          {children}
        </div>
      </div>
    </div>
  );
}
