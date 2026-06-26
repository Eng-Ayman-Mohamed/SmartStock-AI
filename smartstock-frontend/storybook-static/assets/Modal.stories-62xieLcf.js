import{i as e,s as t}from"./preload-helper-xPQekRTU.js";import{t as n}from"./react-CnPKFcMr.js";import{x as r}from"./iframe-DD82_D2a.js";import{n as i,t as a}from"./lucide-react-BXoma8fF.js";import{n as o,t as s}from"./Button-U1y0I8Ib.js";function c({open:e,onClose:t,title:n,children:r,footer:a}){let o=(0,l.useRef)(null);return(0,l.useEffect)(()=>{if(!e)return;let n=e=>{e.key===`Escape`&&t()};return document.addEventListener(`keydown`,n),document.body.style.overflow=`hidden`,()=>{document.removeEventListener(`keydown`,n),document.body.style.overflow=``}},[e,t]),e?(0,u.jsx)(`div`,{ref:o,className:`fixed inset-0 z-50 flex items-center justify-center bg-black/30 dark:bg-black/50 animate-fadeIn`,onClick:e=>{e.target===o.current&&t()},role:`dialog`,"aria-modal":`true`,"aria-label":n,children:(0,u.jsxs)(`div`,{className:`bg-canvas rounded-lg shadow-elevated w-full max-w-lg mx-4 animate-slideUp flex flex-col max-h-[90vh]`,children:[n&&(0,u.jsxs)(`div`,{className:`flex items-center justify-between px-4 sm:px-6 pt-4 sm:pt-6 pb-4 border-b border-hairline shrink-0`,children:[(0,u.jsx)(`h2`,{className:`text-section-heading text-ink min-w-0 mr-3 truncate`,children:n}),(0,u.jsx)(`button`,{onClick:t,className:`flex items-center justify-center w-7 h-7 rounded-md text-ink-faint hover:text-ink-secondary hover:bg-canvas-soft transition-colors shrink-0`,"aria-label":`Close dialog`,children:(0,u.jsx)(i,{className:`w-4 h-4`})})]}),(0,u.jsx)(`div`,{className:`px-4 sm:px-6 py-4 sm:py-6 overflow-y-auto flex-1 min-h-0`,children:r}),a&&(0,u.jsx)(`div`,{className:`px-4 sm:px-6 pb-4 sm:pb-6 pt-4 border-t border-hairline flex flex-wrap items-center justify-end gap-2 sm:gap-3 shrink-0`,children:a})]})}):null}var l,u,d=e((()=>{l=t(n(),1),a(),u=r(),c.__docgenInfo={description:``,methods:[],displayName:`Modal`,props:{open:{required:!0,tsType:{name:`boolean`},description:``},onClose:{required:!0,tsType:{name:`signature`,type:`function`,raw:`() => void`,signature:{arguments:[],return:{name:`void`}}},description:``},title:{required:!1,tsType:{name:`string`},description:``},children:{required:!0,tsType:{name:`ReactNode`},description:``},footer:{required:!1,tsType:{name:`ReactNode`},description:``}}}})),f,p,m,h,g,_,v,y,b;e((()=>{f=t(n(),1),d(),o(),p=r(),m={title:`Primitives/Modal`,component:c,tags:[`autodocs`],argTypes:{open:{control:`boolean`},title:{control:`text`}},args:{open:!0,title:`Modal Title`,children:`This is the modal content area.`,onClose:()=>{}}},h={},g={args:{footer:(0,p.jsxs)(`div`,{className:`flex gap-2`,children:[(0,p.jsx)(s,{variant:`secondary`,size:`sm`,children:`Cancel`}),(0,p.jsx)(s,{variant:`primary`,size:`sm`,children:`Confirm`})]})}},_={args:{title:`Terms & Conditions`,children:(0,p.jsx)(`div`,{className:`space-y-4`,children:Array.from({length:15}).map((e,t)=>(0,p.jsxs)(`p`,{children:[`Section `,t+1,`: Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris.`]},t))}),footer:(0,p.jsx)(s,{variant:`primary`,size:`sm`,children:`Accept`})}},v={args:{title:void 0,children:`A modal without a title or header.`}},y={render:e=>{let[t,n]=(0,f.useState)(!1);return(0,p.jsxs)(`div`,{children:[(0,p.jsx)(s,{onClick:()=>n(!0),children:`Open Modal`}),(0,p.jsx)(c,{...e,open:t,onClose:()=>n(!1)})]})},args:{title:`Interactive Modal`,children:`Click outside or press Escape to close.`,footer:(0,p.jsx)(s,{variant:`primary`,size:`sm`,onClick:()=>{},children:`Save`})}},h.parameters={...h.parameters,docs:{...h.parameters?.docs,source:{originalSource:`{}`,...h.parameters?.docs?.source}}},g.parameters={...g.parameters,docs:{...g.parameters?.docs,source:{originalSource:`{
  args: {
    footer: <div className="flex gap-2">
        <Button variant="secondary" size="sm">Cancel</Button>
        <Button variant="primary" size="sm">Confirm</Button>
      </div>
  }
}`,...g.parameters?.docs?.source}}},_.parameters={..._.parameters,docs:{..._.parameters?.docs,source:{originalSource:`{
  args: {
    title: 'Terms & Conditions',
    children: <div className="space-y-4">
        {Array.from({
        length: 15
      }).map((_, i) => <p key={i}>
            Section {i + 1}: Lorem ipsum dolor sit amet, consectetur adipiscing elit.
            Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.
            Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris.
          </p>)}
      </div>,
    footer: <Button variant="primary" size="sm">Accept</Button>
  }
}`,..._.parameters?.docs?.source}}},v.parameters={...v.parameters,docs:{...v.parameters?.docs,source:{originalSource:`{
  args: {
    title: undefined,
    children: 'A modal without a title or header.'
  }
}`,...v.parameters?.docs?.source}}},y.parameters={...y.parameters,docs:{...y.parameters?.docs,source:{originalSource:`{
  render: args => {
    const [open, setOpen] = useState(false);
    return <div>
        <Button onClick={() => setOpen(true)}>Open Modal</Button>
        <Modal {...args} open={open} onClose={() => setOpen(false)} />
      </div>;
  },
  args: {
    title: 'Interactive Modal',
    children: 'Click outside or press Escape to close.',
    footer: <Button variant="primary" size="sm" onClick={() => {}}>Save</Button>
  }
}`,...y.parameters?.docs?.source}}},b=[`Default`,`WithFooter`,`LongContent`,`NoTitle`,`Interactive`]}))();export{h as Default,y as Interactive,_ as LongContent,v as NoTitle,g as WithFooter,b as __namedExportsOrder,m as default};