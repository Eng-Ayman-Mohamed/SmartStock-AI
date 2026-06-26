import{i as e,s as t}from"./preload-helper-xPQekRTU.js";import{t as n}from"./react-CnPKFcMr.js";import{x as r}from"./iframe-DD82_D2a.js";import{Ot as i,o as a,t as o}from"./lucide-react-BXoma8fF.js";function s({sourceDocument:e,page:t,chunkText:n}){let[r,i]=(0,c.useState)(!1),a=(0,c.useRef)(null),o=(0,c.useRef)(null);return(0,c.useEffect)(()=>{if(!r)return;function e(e){a.current&&!a.current.contains(e.target)&&o.current&&!o.current.contains(e.target)&&i(!1)}function t(e){e.key===`Escape`&&i(!1)}return window.document.addEventListener(`mousedown`,e),window.document.addEventListener(`keydown`,t),()=>{window.document.removeEventListener(`mousedown`,e),window.document.removeEventListener(`keydown`,t)}},[r]),(0,l.jsxs)(`span`,{className:`relative inline-block`,children:[(0,l.jsxs)(`button`,{ref:a,type:`button`,onClick:()=>i(e=>!e),onKeyDown:e=>{(e.key===`Enter`||e.key===` `)&&(e.preventDefault(),i(e=>!e))},className:`inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-purple-50 text-purple-800 hover:bg-purple-100 dark:bg-purple-900/30 dark:text-purple-200 dark:hover:bg-purple-900/50 transition-colors cursor-pointer align-middle`,style:{fontSize:`11px`,lineHeight:`16px`},"aria-expanded":r,"aria-label":`Source: ${e}, Page: ${t}`,children:[(0,l.jsx)(`span`,{className:`font-medium`,children:`Source:`}),` `,e,`, Page: `,t]}),r&&n&&(0,l.jsxs)(`div`,{ref:o,role:`tooltip`,className:`absolute z-50 bottom-full left-1/2 -translate-x-1/2 mb-2 w-72 max-w-[calc(100vw-2rem)] p-3 bg-ink text-white text-caption leading-relaxed rounded-lg shadow-elevated`,children:[n,(0,l.jsx)(`div`,{className:`absolute top-full left-1/2 -translate-x-1/2 w-2 h-2 bg-ink rotate-45 -mt-1`})]})]})}var c,l,u=e((()=>{c=t(n(),1),l=r(),s.__docgenInfo={description:``,methods:[],displayName:`CitationTag`,props:{sourceDocument:{required:!0,tsType:{name:`string`},description:``},page:{required:!0,tsType:{name:`number`},description:``},chunkText:{required:!1,tsType:{name:`string`},description:``}}}}));function d(e,t){if(!t||t.length===0)return e;let n=[];m.lastIndex=0;let r,i=0;for(;(r=m.exec(e))!==null;){r.index>i&&n.push(e.slice(i,r.index));let a=r[1].trim(),o=parseInt(r[2],10),c=t.find(e=>e.document===a&&e.page===o);n.push((0,p.jsx)(s,{sourceDocument:a,page:o,chunkText:c?.chunk_text},`${a}-${o}-${r.index}`)),i=r.index+r[0].length}return i<e.length&&n.push(e.slice(i)),n.length>0?n:e}var f,p,m,h,g=e((()=>{f=t(n(),1),o(),u(),p=r(),m=/\[Source:\s*([^,]+),\s*Page:\s*(\d+)\]/g,h=(0,f.memo)(function({message:e}){let t=e.role===`user`,n=(0,f.useMemo)(()=>t?e.text:d(e.text,e.sources),[t,e.text,e.sources]);return!t&&!e.text?null:(0,p.jsxs)(`div`,{className:`flex gap-2.5 animate-fadeIn ${t?`flex-row-reverse`:``}`,children:[(0,p.jsx)(`div`,{className:`flex items-center justify-center w-7 h-7 rounded-full shrink-0 ${t?`bg-brand-600`:`bg-purple-50 dark:bg-purple-900/30`}`,children:t?(0,p.jsx)(a,{className:`w-3.5 h-3.5 text-white`}):(0,p.jsx)(i,{className:`w-3.5 h-3.5 text-purple-600 dark:text-purple-400`})}),(0,p.jsx)(`div`,{className:`max-w-[75%] min-w-0 ${t?`text-right`:``}`,children:(0,p.jsx)(`div`,{className:`inline-block text-left ${t?`bg-brand-600 text-white rounded-2xl rounded-br-md px-4 py-2.5`:`bg-canvas-soft text-ink rounded-2xl rounded-bl-md px-4 py-2.5 border border-hairline/50`}`,children:(0,p.jsx)(`p`,{className:`text-body leading-relaxed whitespace-pre-wrap break-words`,children:n})})})]})}),h.__docgenInfo={description:``,methods:[],displayName:`MessageBubble`,props:{message:{required:!0,tsType:{name:`Message`},description:``}}}})),_,v,y,b,x,S,C;e((()=>{g(),_={title:`AI Assistant/MessageBubble`,component:h,tags:[`autodocs`]},v={args:{message:{id:`1`,role:`user`,text:`What products are low on stock?`,timestamp:Date.now()}}},y={args:{message:{id:`2`,role:`ai`,text:`I found 3 products that are currently low on stock:
1. Widget Beta (8 units remaining)
2. Gadget Gamma (0 units)
3. Component Zeta (3 units)`,timestamp:Date.now()}}},b={args:{message:{id:`3`,role:`ai`,text:`Based on the supplier agreement [Source: Supplier Contract Q1, Page: 12], the lead time for Widget Beta is 14 days.`,sources:[{document:`Supplier Contract Q1`,page:12,chunk_text:`Lead time for standard widgets is 14 business days from order confirmation.`}],timestamp:Date.now()}}},x={args:{message:{id:`4`,role:`ai`,text:`According to [Source: Inventory Report, Page: 5] and [Source: Supplier Guidelines, Page: 23], the reorder point should be set to 50 units.`,sources:[{document:`Inventory Report`,page:5,chunk_text:`Historical data shows optimal reorder point is 50 units for this SKU.`},{document:`Supplier Guidelines`,page:23,chunk_text:`Minimum order quantity is 50 units for standard products.`}],timestamp:Date.now()}}},S={args:{message:{id:`5`,role:`ai`,text:``,timestamp:Date.now()}}},v.parameters={...v.parameters,docs:{...v.parameters?.docs,source:{originalSource:`{
  args: {
    message: {
      id: '1',
      role: 'user',
      text: 'What products are low on stock?',
      timestamp: Date.now()
    } satisfies Message
  }
}`,...v.parameters?.docs?.source}}},y.parameters={...y.parameters,docs:{...y.parameters?.docs,source:{originalSource:`{
  args: {
    message: {
      id: '2',
      role: 'ai',
      text: 'I found 3 products that are currently low on stock:\\n1. Widget Beta (8 units remaining)\\n2. Gadget Gamma (0 units)\\n3. Component Zeta (3 units)',
      timestamp: Date.now()
    } satisfies Message
  }
}`,...y.parameters?.docs?.source}}},b.parameters={...b.parameters,docs:{...b.parameters?.docs,source:{originalSource:`{
  args: {
    message: {
      id: '3',
      role: 'ai',
      text: 'Based on the supplier agreement [Source: Supplier Contract Q1, Page: 12], the lead time for Widget Beta is 14 days.',
      sources: [{
        document: 'Supplier Contract Q1',
        page: 12,
        chunk_text: 'Lead time for standard widgets is 14 business days from order confirmation.'
      }],
      timestamp: Date.now()
    } satisfies Message
  }
}`,...b.parameters?.docs?.source}}},x.parameters={...x.parameters,docs:{...x.parameters?.docs,source:{originalSource:`{
  args: {
    message: {
      id: '4',
      role: 'ai',
      text: 'According to [Source: Inventory Report, Page: 5] and [Source: Supplier Guidelines, Page: 23], the reorder point should be set to 50 units.',
      sources: [{
        document: 'Inventory Report',
        page: 5,
        chunk_text: 'Historical data shows optimal reorder point is 50 units for this SKU.'
      }, {
        document: 'Supplier Guidelines',
        page: 23,
        chunk_text: 'Minimum order quantity is 50 units for standard products.'
      }],
      timestamp: Date.now()
    } satisfies Message
  }
}`,...x.parameters?.docs?.source}}},S.parameters={...S.parameters,docs:{...S.parameters?.docs,source:{originalSource:`{
  args: {
    message: {
      id: '5',
      role: 'ai',
      text: '',
      timestamp: Date.now()
    } satisfies Message
  }
}`,...S.parameters?.docs?.source}}},C=[`UserMessage`,`AISimple`,`AIWithCitation`,`AIMultipleCitations`,`AIStreamingPlaceholder`]}))();export{x as AIMultipleCitations,y as AISimple,S as AIStreamingPlaceholder,b as AIWithCitation,v as UserMessage,C as __namedExportsOrder,_ as default};