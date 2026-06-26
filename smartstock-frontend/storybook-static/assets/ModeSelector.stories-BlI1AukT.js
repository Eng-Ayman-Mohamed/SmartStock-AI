import{i as e,s as t}from"./preload-helper-xPQekRTU.js";import{t as n}from"./react-CnPKFcMr.js";import{x as r}from"./iframe-DD82_D2a.js";function i({active:e,onChange:t}){return(0,a.jsx)(`div`,{className:`flex flex-wrap items-center gap-1 px-1 py-1 bg-canvas-soft rounded-lg`,role:`radiogroup`,"aria-label":`Chat mode`,children:o.map(n=>(0,a.jsx)(`button`,{type:`button`,role:`radio`,"aria-checked":e===n.key,onClick:()=>t(n.key),className:`px-3 py-1.5 rounded-md text-caption font-medium transition-all ${e===n.key?`bg-brand-600 text-white shadow-sm`:`text-ink-muted hover:text-ink hover:bg-canvas`}`,children:n.label},n.key))})}var a,o,s=e((()=>{a=r(),o=[{key:`auto`,label:`Ask AI`},{key:`nl_query`,label:`NL Query`},{key:`rag`,label:`Search Documents`}],i.__docgenInfo={description:``,methods:[],displayName:`ModeSelector`,props:{active:{required:!0,tsType:{name:`union`,raw:`'auto' | 'nl_query' | 'rag'`,elements:[{name:`literal`,value:`'auto'`},{name:`literal`,value:`'nl_query'`},{name:`literal`,value:`'rag'`}]},description:``},onChange:{required:!0,tsType:{name:`signature`,type:`function`,raw:`(mode: ChatMode) => void`,signature:{arguments:[{type:{name:`union`,raw:`'auto' | 'nl_query' | 'rag'`,elements:[{name:`literal`,value:`'auto'`},{name:`literal`,value:`'nl_query'`},{name:`literal`,value:`'rag'`}]},name:`mode`}],return:{name:`void`}}},description:``}}}})),c,l,u,d,f,p,m,h;e((()=>{c=t(n(),1),s(),l=r(),u={title:`AI Assistant/ModeSelector`,component:i,tags:[`autodocs`],args:{active:`auto`,onChange:e=>console.log(`Mode:`,e)}},d={args:{active:`auto`}},f={args:{active:`nl_query`}},p={args:{active:`rag`}},m={render:e=>{let[t,n]=(0,c.useState)(`auto`);return(0,l.jsx)(i,{...e,active:t,onChange:n})}},d.parameters={...d.parameters,docs:{...d.parameters?.docs,source:{originalSource:`{
  args: {
    active: 'auto'
  }
}`,...d.parameters?.docs?.source}}},f.parameters={...f.parameters,docs:{...f.parameters?.docs,source:{originalSource:`{
  args: {
    active: 'nl_query'
  }
}`,...f.parameters?.docs?.source}}},p.parameters={...p.parameters,docs:{...p.parameters?.docs,source:{originalSource:`{
  args: {
    active: 'rag'
  }
}`,...p.parameters?.docs?.source}}},m.parameters={...m.parameters,docs:{...m.parameters?.docs,source:{originalSource:`{
  render: args => {
    const [active, setActive] = useState<ChatMode>('auto');
    return <ModeSelector {...args} active={active} onChange={setActive} />;
  }
}`,...m.parameters?.docs?.source}}},h=[`Auto`,`NLQuery`,`RAG`,`Interactive`]}))();export{d as Auto,m as Interactive,f as NLQuery,p as RAG,h as __namedExportsOrder,u as default};