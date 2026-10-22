export const HOME_PANELS = ['agenda', 'checkin', 'welcome', 'progress', 'minutes', 'calories', 'weight', 'streak']
export function panelOrder(saved) {
  const known = new Set(HOME_PANELS)
  const valid = Array.isArray(saved) ? saved.filter(id => known.has(id)) : []
  return [...new Set([...valid, ...HOME_PANELS])]
}
export function movePanel(saved, source, target) {
  const order = panelOrder(saved)
  if (!order.includes(source) || !order.includes(target) || source === target) return order
  const to = order.indexOf(target)
  order.splice(order.indexOf(source), 1);order.splice(to, 0, source)
  return order
}
