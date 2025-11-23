import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ReferenceArea,
} from 'recharts';
import { MetricDataPoint, MetricForecastPoint } from '../../types/metrics';

interface Props {
  history: MetricDataPoint[];
  forecast: MetricForecastPoint[];
}

export default function ForecastChart({ history, forecast }: Props) {
  const combined = [
    ...history.map((d) => ({ ...d, type: 'history' })),
    ...forecast.map((d) => ({ value: d.forecast, ds: d.ds, lower: d.lower, upper: d.upper, type: 'forecast' })),
  ];

  return (
    <ResponsiveContainer width="100%" height={340}>
      <LineChart data={combined} margin={{ left: 10, right: 10, top: 20, bottom: 10 }}>
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis dataKey="ds" tick={{ fontSize: 12 }} />
        <YAxis tick={{ fontSize: 12 }} />
        <Tooltip />
        <Legend />
        <ReferenceArea ifOverflow="hidden" x1={history[history.length - 1]?.ds} stroke="rgba(0,0,0,0.2)" />
        <Line name="Historical" type="monotone" dataKey="value" stroke="#0B3D91" dot={false} strokeWidth={2} />
        <Line name="Forecast" type="monotone" dataKey={(d) => (d.type === 'forecast' ? d.value : null)} stroke="#1F6FEB" dot={false} strokeDasharray="5 4" />
      </LineChart>
    </ResponsiveContainer>
  );
}
