import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { BarChart, PieChart } from 'echarts/charts'
import { GridComponent, LegendComponent, TooltipComponent } from 'echarts/components'

use([CanvasRenderer, BarChart, PieChart, GridComponent, LegendComponent, TooltipComponent])

export const RESULT_COLORS = {
  Autorizado: '#16a34a',
  Denegado: '#dc1f26',
  'No registrado': '#d98a00',
  'Verificación manual': '#2156e8',
}
// Colores de texto y rejilla según el tema (claro u oscuro).
export function chartTheme(dark) {
  return {
    text: dark ? '#c9d4e8' : '#2b3a55',
    grid: dark ? '#26406b' : '#e6ebf3',
    surface: dark ? '#13264a' : '#ffffff',
  }
}
export function baseOption(dark) {
  const t = chartTheme(dark)
  return {
    textStyle: { fontFamily: 'Inter, system-ui, sans-serif', color: t.text },
    tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
    legend: { bottom: 0, icon: 'roundRect', textStyle: { color: t.text } },
    grid: { left: 40, right: 16, top: 16, bottom: 48 },
  }
}
