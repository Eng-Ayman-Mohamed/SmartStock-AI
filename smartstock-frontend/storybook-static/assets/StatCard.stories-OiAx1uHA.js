import{i as e}from"./preload-helper-xPQekRTU.js";import{x as t}from"./iframe-DD82_D2a.js";import{M as n,i as r,ot as i,t as a,u as o}from"./lucide-react-BXoma8fF.js";function s({label:e,value:t,trend:n,icon:r,accent:i=`none`}){return(0,c.jsxs)(`div`,{className:`bg-canvas rounded-lg border border-hairline p-4 sm:p-6 min-h-24 min-w-0 flex flex-col justify-between ${l[i]}`,children:[(0,c.jsxs)(`div`,{className:`flex items-center justify-between gap-2`,children:[(0,c.jsx)(`span`,{className:`text-caption font-medium text-ink-muted uppercase tracking-[0.05em] min-w-0 truncate`,children:e}),r&&(0,c.jsx)(r,{className:`w-4 h-4 text-ink-faint shrink-0`,"aria-hidden":`true`})]}),(0,c.jsxs)(`div`,{className:`flex items-end justify-between gap-2 mt-2`,children:[(0,c.jsx)(`span`,{className:`text-[22px] sm:text-[26px] font-medium text-ink tabular-nums leading-none min-w-0 truncate`,children:t}),n&&(0,c.jsxs)(`span`,{className:`text-caption tabular-nums ${n.direction===`up`?n.color||`text-green-600`:n.color||`text-red-600`}`,children:[n.direction===`up`?`↑`:`↓`,` `,n.percentage]})]})]})}var c,l,u=e((()=>{c=t(),l={orange:`border-l-2 border-l-orange-600`,purple:`border-l-2 border-l-purple-600`,green:`border-l-2 border-l-green-600`,red:`border-l-2 border-l-red-600`,none:``},s.__docgenInfo={description:``,methods:[],displayName:`StatCard`,props:{label:{required:!0,tsType:{name:`string`},description:``},value:{required:!0,tsType:{name:`union`,raw:`string | number`,elements:[{name:`string`},{name:`number`}]},description:``},trend:{required:!1,tsType:{name:`signature`,type:`object`,raw:`{
  direction: 'up' | 'down';
  percentage: string;
  color?: string;
}`,signature:{properties:[{key:`direction`,value:{name:`union`,raw:`'up' | 'down'`,elements:[{name:`literal`,value:`'up'`},{name:`literal`,value:`'down'`}],required:!0}},{key:`percentage`,value:{name:`string`,required:!0}},{key:`color`,value:{name:`string`,required:!1}}]}},description:``},icon:{required:!1,tsType:{name:`LucideIcon`},description:``},accent:{required:!1,tsType:{name:`union`,raw:`'orange' | 'purple' | 'green' | 'red' | 'none'`,elements:[{name:`literal`,value:`'orange'`},{name:`literal`,value:`'purple'`},{name:`literal`,value:`'green'`},{name:`literal`,value:`'red'`},{name:`literal`,value:`'none'`}]},description:``,defaultValue:{value:`'none'`,computed:!1}}}}})),d,f,p,m,h,g,_,v,y;e((()=>{a(),u(),d={title:`Primitives/StatCard`,component:s,tags:[`autodocs`],argTypes:{accent:{control:`select`,options:[`orange`,`purple`,`green`,`red`,`none`]}},args:{label:`Total Products`,value:`1,234`}},f={},p={args:{label:`Total Products`,value:`1,234`,icon:n}},m={args:{label:`Revenue`,value:`$48,290`,icon:i,trend:{direction:`up`,percentage:`12.5%`}}},h={args:{label:`Stockouts`,value:`23`,icon:o,trend:{direction:`down`,percentage:`8.1%`}}},g={args:{label:`Active Users`,value:`892`,icon:r,accent:`green`,trend:{direction:`up`,percentage:`5.2%`}}},_={args:{label:`Overdue Orders`,value:`12`,accent:`red`,trend:{direction:`up`,percentage:`3.1%`,color:`text-red-600`}}},v={args:{label:`AI Predictions`,value:`96%`,icon:n,accent:`purple`,trend:{direction:`up`,percentage:`2.4%`}}},f.parameters={...f.parameters,docs:{...f.parameters?.docs,source:{originalSource:`{}`,...f.parameters?.docs?.source}}},p.parameters={...p.parameters,docs:{...p.parameters?.docs,source:{originalSource:`{
  args: {
    label: 'Total Products',
    value: '1,234',
    icon: Package
  }
}`,...p.parameters?.docs?.source}}},m.parameters={...m.parameters,docs:{...m.parameters?.docs,source:{originalSource:`{
  args: {
    label: 'Revenue',
    value: '$48,290',
    icon: DollarSign,
    trend: {
      direction: 'up',
      percentage: '12.5%'
    }
  }
}`,...m.parameters?.docs?.source}}},h.parameters={...h.parameters,docs:{...h.parameters?.docs,source:{originalSource:`{
  args: {
    label: 'Stockouts',
    value: '23',
    icon: AlertTriangle,
    trend: {
      direction: 'down',
      percentage: '8.1%'
    }
  }
}`,...h.parameters?.docs?.source}}},g.parameters={...g.parameters,docs:{...g.parameters?.docs,source:{originalSource:`{
  args: {
    label: 'Active Users',
    value: '892',
    icon: Users,
    accent: 'green',
    trend: {
      direction: 'up',
      percentage: '5.2%'
    }
  }
}`,...g.parameters?.docs?.source}}},_.parameters={..._.parameters,docs:{..._.parameters?.docs,source:{originalSource:`{
  args: {
    label: 'Overdue Orders',
    value: '12',
    accent: 'red',
    trend: {
      direction: 'up',
      percentage: '3.1%',
      color: 'text-red-600'
    }
  }
}`,..._.parameters?.docs?.source}}},v.parameters={...v.parameters,docs:{...v.parameters?.docs,source:{originalSource:`{
  args: {
    label: 'AI Predictions',
    value: '96%',
    icon: Package,
    accent: 'purple',
    trend: {
      direction: 'up',
      percentage: '2.4%'
    }
  }
}`,...v.parameters?.docs?.source}}},y=[`Default`,`WithIcon`,`UpwardTrend`,`DownwardTrend`,`GreenAccent`,`RedAccent`,`PurpleAccent`]}))();export{f as Default,h as DownwardTrend,g as GreenAccent,v as PurpleAccent,_ as RedAccent,m as UpwardTrend,p as WithIcon,y as __namedExportsOrder,d as default};