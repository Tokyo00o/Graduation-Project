import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts';

interface Props {
  data: { name: string; value: number }[];
}

export default function ASRChart({ data }: Props) {
  return (
    <ResponsiveContainer width="100%" height={250}>
      <LineChart data={data}>
        <XAxis dataKey="name" stroke="#8b8fa3" fontSize={11} />
        <YAxis stroke="#8b8fa3" fontSize={11} domain={[0, 1]} tickFormatter={v => `${(v * 100).toFixed(0)}%`} />
        <Tooltip
          contentStyle={{ background: '#1a1d27', border: '1px solid #2a2e3a', borderRadius: 6, fontSize: 12 }}
          formatter={(v: number) => `${(v * 100).toFixed(1)}%`}
        />
        <Line type="monotone" dataKey="value" stroke="#6366f1" strokeWidth={2} dot={{ r: 3 }} />
      </LineChart>
    </ResponsiveContainer>
  );
}
