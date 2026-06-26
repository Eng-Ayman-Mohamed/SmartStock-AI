import{i as e,s as t}from"./preload-helper-xPQekRTU.js";import{t as n}from"./react-CnPKFcMr.js";import{x as r}from"./iframe-DD82_D2a.js";import{X as i,n as a,t as o,u as s}from"./lucide-react-BXoma8fF.js";function c({alert:e,onDismiss:t}){let[n,r]=(0,l.useState)(!1),o=e.severity===`critical`;return(0,u.jsxs)(`div`,{className:`flex items-start gap-3 px-4 py-3 rounded-xl border backdrop-blur-sm transition-all duration-200 ease-out ${n?`opacity-0 translate-x-4 max-h-0 py-0 mb-0 overflow-hidden border-transparent`:`animate-slideUp`} ${o?`bg-red-50 border-red-200 text-red-800 dark:bg-red-900/30 dark:border-red-800 dark:text-red-200`:`bg-orange-50 border-orange-200 text-orange-800 dark:bg-orange-900/30 dark:border-orange-800 dark:text-orange-200`}`,onTransitionEnd:r=>{r.propertyName===`opacity`&&n&&t(e.sku.id)},children:[o?(0,u.jsx)(s,{className:`w-5 h-5 shrink-0 mt-0.5`}):(0,u.jsx)(i,{className:`w-5 h-5 shrink-0 mt-0.5`}),(0,u.jsx)(`p`,{className:`text-sm flex-1`,children:e.message}),(0,u.jsx)(`button`,{onClick:()=>{r(!0)},className:`shrink-0 p-0.5 rounded hover:bg-black/10 dark:hover:bg-white/10 transition-colors`,"aria-label":`Dismiss alert`,children:(0,u.jsx)(a,{className:`w-4 h-4`})})]})}var l,u,d=e((()=>{l=t(n(),1),o(),u=r(),c.__docgenInfo={description:``,methods:[],displayName:`AlertBanner`,props:{alert:{required:!0,tsType:{name:`AlertInfo`},description:``},onDismiss:{required:!0,tsType:{name:`signature`,type:`function`,raw:`(id: string) => void`,signature:{arguments:[{type:{name:`string`},name:`id`}],return:{name:`void`}}},description:``}}}})),f,p,m,h,g;e((()=>{d(),f={id:`1`,sku_code:`WID-001`,product_name:`Widget Alpha`,current_stock:5,reorder_point:20,predicted_demand_30d:45},p={title:`Forecasting/AlertBanner`,component:c,tags:[`autodocs`],args:{onDismiss:e=>console.log(`Dismissed:`,e)}},m={args:{alert:{sku:f,severity:`critical`,message:`Widget Alpha stock is at 5 — below reorder point of 20. Consider ordering soon.`}}},h={args:{alert:{sku:{...f,current_stock:18},severity:`warning`,message:`Widget Alpha has only 18 units, which may be insufficient for the forecasted 30-day demand of 45.`}}},m.parameters={...m.parameters,docs:{...m.parameters?.docs,source:{originalSource:`{
  args: {
    alert: {
      sku: mockSku,
      severity: 'critical',
      message: 'Widget Alpha stock is at 5 — below reorder point of 20. Consider ordering soon.'
    }
  }
}`,...m.parameters?.docs?.source}}},h.parameters={...h.parameters,docs:{...h.parameters?.docs,source:{originalSource:`{
  args: {
    alert: {
      sku: {
        ...mockSku,
        current_stock: 18
      },
      severity: 'warning',
      message: 'Widget Alpha has only 18 units, which may be insufficient for the forecasted 30-day demand of 45.'
    }
  }
}`,...h.parameters?.docs?.source}}},g=[`Critical`,`Warning`]}))();export{m as Critical,h as Warning,g as __namedExportsOrder,p as default};