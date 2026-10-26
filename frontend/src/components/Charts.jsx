import {
  ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip, CartesianGrid, Legend, PieChart, Pie, Cell, LineChart, Line, ComposedChart,
} from "recharts";
import { money, num } from "@/lib/api";

export const COLORS = ["#F59E0B", "#06B6D4", "#10B981", "#F43F5E", "#A3E635", "#FB923C", "#38BDF8", "#E879F9", "#94A3B8"];
const axis = { stroke: "#475569", fontSize: 11, fontFamily: "JetBrains Mono, monospace", tickLine: false, axisLine: false };
const tip = {
  contentStyle: { background: "#0B0F17", border: "1px solid #334155", borderRadius: 6, fontSize: 12 },
  labelStyle: { color: "#F59E0B", fontFamily: "JetBrains Mono, monospace" },
  itemStyle: { color: "#E2E8F0" },
  cursor: { fill: "rgba(148,163,184,0.06)" },
};
export const short = (v) => (Math.abs(v) >= 1000 ? `$${(v / 1000).toFixed(0)}k` : `$${Math.round(v)}`);

function Empty() {
  return <div className="flex h-full items-center justify-center font-mono text-xs text-slate-600">No data yet</div>;
}

export function IncomeExpenseChart({ data }) {
  if (!data?.length) return <Empty />;
  return (
    <ResponsiveContainer width="100%" height="100%">
      <BarChart data={data} barGap={4}>
        <CartesianGrid stroke="#1F2937" vertical={false} />
        <XAxis dataKey="m" {...axis} />
        <YAxis {...axis} tickFormatter={short} width={50} />
        <Tooltip {...tip} formatter={(v) => money(v)} />
        <Legend wrapperStyle={{ fontSize: 12 }} />
        <Bar dataKey="income" name="Income" fill="#10B981" radius={[3, 3, 0, 0]} />
        <Bar dataKey="expenses" name="Expenses" fill="#F43F5E" radius={[3, 3, 0, 0]} />
      </BarChart>
    </ResponsiveContainer>
  );
}

export function CategoryPie({ data }) {
  if (!data?.length) return <Empty />;
  return (
    <ResponsiveContainer width="100%" height="100%">
      <PieChart>
        <Pie data={data} dataKey="value" nameKey="name" innerRadius="55%" outerRadius="85%" paddingAngle={2} stroke="none">
          {data.map((_, i) => <Cell key={i} fill={COLORS[i % COLORS.length]} />)}
        </Pie>
        <Tooltip {...tip} formatter={(v) => money(v)} />
        <Legend wrapperStyle={{ fontSize: 11 }} layout="vertical" align="right" verticalAlign="middle" />
      </PieChart>
    </ResponsiveContainer>
  );
}

export function FuelTrendChart({ data }) {
  if (!data?.length) return <Empty />;
  return (
    <ResponsiveContainer width="100%" height="100%">
      <ComposedChart data={data}>
        <CartesianGrid stroke="#1F2937" vertical={false} />
        <XAxis dataKey="m" {...axis} />
        <YAxis yAxisId="l" {...axis} tickFormatter={short} width={50} />
        <YAxis yAxisId="r" orientation="right" {...axis} domain={["auto", "auto"]} width={36} />
        <Tooltip {...tip} formatter={(v, n) => (n === "Fuel cost" ? money(v) : num(v, 2))} />
        <Legend wrapperStyle={{ fontSize: 12 }} />
        <Bar yAxisId="l" dataKey="cost" name="Fuel cost" fill="#F59E0B" fillOpacity={0.7} radius={[3, 3, 0, 0]} />
        <Line yAxisId="r" dataKey="avg_mpg" name="Avg MPG" stroke="#06B6D4" strokeWidth={2} dot={{ r: 3 }} />
      </ComposedChart>
    </ResponsiveContainer>
  );
}

export function DriverBars({ data, dataKey, name, color = "#F59E0B", fmt = (v) => v, tickFmt }) {
  if (!data?.length) return <Empty />;
  return (
    <ResponsiveContainer width="100%" height="100%">
      <BarChart data={data} layout="vertical" margin={{ left: 10, right: 24 }}>
        <CartesianGrid stroke="#1F2937" horizontal={false} />
        <XAxis type="number" {...axis} tickFormatter={tickFmt || fmt} tickCount={5} />
        <YAxis type="category" dataKey="name" {...axis} width={130} tick={{ fill: "#CBD5E1", fontSize: 11 }} />
        <Tooltip {...tip} formatter={(v) => fmt(v)} />
        <Bar dataKey={dataKey} name={name} fill={color} radius={[0, 3, 3, 0]} />
      </BarChart>
    </ResponsiveContainer>
  );
}

export function SimpleLine({ data, x, y, name, color = "#06B6D4", fmt = (v) => v }) {
  if (!data?.length) return <Empty />;
  return (
    <ResponsiveContainer width="100%" height="100%">
      <LineChart data={data}>
        <CartesianGrid stroke="#1F2937" vertical={false} />
        <XAxis dataKey={x} {...axis} />
        <YAxis {...axis} domain={["auto", "auto"]} width={45} tickFormatter={fmt} />
        <Tooltip {...tip} formatter={(v) => fmt(v)} />
        <Line dataKey={y} name={name} stroke={color} strokeWidth={2} dot={{ r: 3 }} />
      </LineChart>
    </ResponsiveContainer>
  );
}

export function SimplePie({ data, nameKey, dataKey, colors }) {
  if (!data?.length) return <Empty />;
  return (
    <ResponsiveContainer width="100%" height="100%">
      <PieChart>
        <Pie data={data} dataKey={dataKey} nameKey={nameKey} innerRadius="50%" outerRadius="85%" paddingAngle={2} stroke="none">
          {data.map((d, i) => <Cell key={i} fill={(colors && colors[d[nameKey]]) || COLORS[i % COLORS.length]} />)}
        </Pie>
        <Tooltip {...tip} />
        <Legend wrapperStyle={{ fontSize: 11 }} />
      </PieChart>
    </ResponsiveContainer>
  );
}
