import os
os.chdir("/app/frontend/src")


def sub(path, pairs):
    s = open(path).read()
    for a, b in pairs:
        assert a in s, (path, a)
        s = s.replace(a, b)
    open(path, "w").write(s)


sub("context/AuthContext.js", [("<AuthCtx.Provider value={{ user, login, logout }}>", "<AuthCtx.Provider value={{ user, login, logout, isOwner: user?.role === \"owner\" }}>")])
sub("components/Layout.jsx", [
    ('  { to: "/test-data", label: "Test Data", icon: Database, id: "test-data" },', '  { to: "/report", label: "Monthly Report", icon: FileText, id: "report" },\n  { to: "/test-data", label: "Test Data", icon: Database, id: "test-data", owner: true },'),
    ('  { to: "/users", label: "Users", icon: UserCog, id: "users" },', '  { to: "/users", label: "Users", icon: UserCog, id: "users", owner: true },'),
    ("Trophy, UserCog,", "Trophy, UserCog, FileText,"),
    ("  const { user, logout } = useAuth();", "  const { user, logout, isOwner } = useAuth();"),
    ("        {NAV.map(({ to, label, icon: Icon, id }) => (", "        {NAV.filter((n) => isOwner || !n.owner).map(({ to, label, icon: Icon, id }) => ("),
    ('<span className="text-slate-300" data-testid="current-username">{user?.username}</span>', '<span className="text-slate-300" data-testid="current-username">{user?.username}</span>\n          <span data-testid="current-role" className="ml-2 rounded bg-red-500/10 px-1.5 py-0.5 text-[10px] uppercase text-red-400">{user?.role}</span>'),
    ('const NO_RANGE = ["/leaderboard", "/users", "/test-data"];', 'const NO_RANGE = ["/leaderboard", "/users", "/test-data", "/report"];'),
    ('<aside className="fixed inset-y-0 left-0 z-40 hidden w-64', '<aside className="no-print fixed inset-y-0 left-0 z-40 hidden w-64'),
    ('<div className="sticky top-0 z-30 flex items-center', '<div className="no-print sticky top-0 z-30 flex items-center'),
])
sub("components/CrudPage.jsx", [
    ('import { useFetch, useLookups } from "@/hooks/useData";', 'import { useFetch, useLookups } from "@/hooks/useData";\nimport { useAuth } from "@/context/AuthContext";'),
    ("  const range = useDateRange();\n", "  const range = useDateRange();\n  const { isOwner } = useAuth();\n"),
    ('                    <button data-testid={`delete-${slug}-${r.id}`}', '                    {isOwner && <button data-testid={`delete-${slug}-${r.id}`}'),
    ('<Trash2 className="h-4 w-4" /></button>\n                  </td>', '<Trash2 className="h-4 w-4" /></button>}\n                  </td>'),
])
sub("pages/CategoryManager.jsx", [
    ('import { Panel } from "@/components/Bits";', 'import { Panel } from "@/components/Bits";\nimport { useAuth } from "@/context/AuthContext";'),
    ("  const [edit, setEdit] = useState(false);", "  const [edit, setEdit] = useState(false);\n  const { isOwner } = useAuth();"),
    ('          <button data-testid={`category-delete-${cat.id}`}', '          {isOwner && <button data-testid={`category-delete-${cat.id}`}'),
    ('<Trash2 className="h-3 w-3" /></button>', '<Trash2 className="h-3 w-3" /></button>}'),
])
sub("pages/Users.jsx", [
    ('const [form, setForm] = useState({ username: "", password: "", confirm: "" });', 'const [form, setForm] = useState({ username: "", password: "", confirm: "", role: "dispatcher" });'),
    ('await api.post("/users", { username: form.username, password: form.password });', 'await api.post("/users", { username: form.username, password: form.password, role: form.role });'),
    ('setForm({ username: "", password: "", confirm: "" });', 'setForm({ username: "", password: "", confirm: "", role: "dispatcher" });'),
    ('            {field("confirm", "Confirm password", "password")}', '''            {field("confirm", "Confirm password", "password")}
            <div className="space-y-1.5">
              <div className="font-mono text-[11px] uppercase tracking-wider text-slate-400">Role</div>
              <div className="grid grid-cols-2 gap-2" data-testid="new-user-role">
                {[["dispatcher", "Dispatcher", "Logs and edits records. Can't delete data or manage users."], ["owner", "Owner", "Full control, including users and deleting data."]].map(([v, l, d]) => (
                  <button type="button" key={v} data-testid={`new-user-role-${v}`} onClick={() => setForm({ ...form, role: v })}
                    className={`rounded-md border p-3 text-left transition-colors ${form.role === v ? "border-blue-500 bg-blue-500/10" : "border-slate-700 hover:border-slate-500"}`}>
                    <div className="text-sm font-semibold">{l}</div>
                    <div className="mt-1 text-[11px] text-slate-500">{d}</div>
                  </button>
                ))}
              </div>
            </div>'''),
    ('{u.id === user?.id && <span', '<span className={`ml-2 rounded px-1.5 py-0.5 text-[10px] uppercase ${u.role === "owner" ? "bg-red-500/10 text-red-400" : "bg-blue-500/10 text-blue-400"}`} data-testid={`user-role-${u.username}`}>{u.role}</span>{u.id === user?.id && <span'),
])
sub("App.js", [
    ('import Users from "@/pages/Users";', 'import Users from "@/pages/Users";\nimport Report from "@/pages/Report";'),
    ('            <Route path="/users" element={<Users />} />', '            <Route path="/users" element={<Users />} />\n            <Route path="/report" element={<Report />} />'),
])
sub("pages/Leaderboard.jsx", [
    ("      {ranked.length > 0 && (\n        <div className=\"grid gap-6 lg:grid-cols-3\">", "      {ranked.length > 0 && (\n        <div className=\"mb-6 grid gap-6 lg:grid-cols-3\">"),
    ("          {METRICS.map((m) => <RankList key={m.key} metric={m} drivers={ranked} />)}\n        </div>\n      )}\n", "          {METRICS.map((m) => <RankList key={m.key} metric={m} drivers={ranked} />)}\n        </div>\n      )}\n      <LeaderboardHistory onPick={setMonth} />\n"),
    ('import { PageHeader, Panel } from "@/components/Bits";', 'import { PageHeader, Panel } from "@/components/Bits";\nimport LeaderboardHistory from "@/pages/LeaderboardHistory";'),
])
s = open("index.css").read()
s += """
@media print {
    .no-print { display: none !important; }
    main { padding-left: 0 !important; }
    body, .min-h-screen { background: #fff !important; }
    @page { size: letter; margin: 0.4in; }
}
"""
open("index.css", "w").write(s)
print("ok")
