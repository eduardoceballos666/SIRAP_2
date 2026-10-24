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
export const BASE = {
  textStyle: { fontFamily: 'Inter, system-ui, sans-serif', color: '#2b3a55' },
  tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
  legend: { bottom: 0, icon: 'roundRect' },
  grid: { left: 40, right: 16, top: 16, bottom: 48 },
}
