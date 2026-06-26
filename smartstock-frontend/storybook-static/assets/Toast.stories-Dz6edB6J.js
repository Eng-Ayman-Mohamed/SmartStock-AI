import{i as e,s as t}from"./preload-helper-xPQekRTU.js";import{t as n}from"./react-CnPKFcMr.js";import{a as r,o as i,x as a}from"./iframe-DD82_D2a.js";import{X as o,ct as s,n as c,t as l,ut as u}from"./lucide-react-BXoma8fF.js";import{n as d,t as f}from"./Button-U1y0I8Ib.js";function p(){let e=i(e=>e.toasts),t=i(e=>e.removeToast);return e.length===0?null:(0,m.jsx)(`div`,{className:`fixed top-4 right-4 z-[100] flex flex-col gap-2 pointer-events-none max-w-[calc(100vw-2rem)]`,"aria-live":`polite`,"aria-label":`Notifications`,children:e.map(e=>{let n=h[e.type];return(0,m.jsxs)(`div`,{className:`pointer-events-auto flex items-start gap-3 px-4 py-3 rounded-lg border border-hairline shadow-soft border-l-[3px] animate-slideUp ${g[e.type]}`,role:`alert`,children:[(0,m.jsx)(n,{className:`w-4 h-4 mt-0.5 shrink-0`,"aria-hidden":`true`}),(0,m.jsx)(`p`,{className:`text-body flex-1`,children:e.message}),(0,m.jsx)(`button`,{onClick:()=>t(e.id),className:`shrink-0 flex items-center justify-center w-5 h-5 rounded-full hover:bg-black/5 dark:hover:bg-white/10 transition-colors`,"aria-label":`Dismiss notification`,children:(0,m.jsx)(c,{className:`w-3 h-3`})})]},e.id)})})}var m,h,g,_=e((()=>{l(),r(),m=a(),h={success:u,error:s,info:o},g={success:`border-l-green-600 bg-green-50 text-green-800 dark:bg-green-900/30 dark:text-green-200 dark:border-l-green-400`,error:`border-l-red-600 bg-red-50 text-red-800 dark:bg-red-900/30 dark:text-red-200 dark:border-l-red-400`,info:`border-l-brand-600 bg-brand-50 text-brand-800 dark:bg-brand-900/30 dark:text-brand-200 dark:border-l-brand-400`},p.__docgenInfo={description:``,methods:[],displayName:`ToastContainer`}}));function v(e,t){i.getState().addToast({type:e,message:t})}var y,b,x,S,C,w,T,E,D;e((()=>{y=t(n(),1),_(),r(),d(),b=a(),x={title:`Primitives/Toast`,component:p,tags:[`autodocs`]},S={render:()=>((0,y.useEffect)(()=>{v(`success`,`Product updated successfully`)},[]),(0,b.jsx)(p,{}))},C={render:()=>((0,y.useEffect)(()=>{v(`error`,`Failed to save changes. Please try again.`)},[]),(0,b.jsx)(p,{}))},w={render:()=>((0,y.useEffect)(()=>{v(`info`,`Your session will expire in 5 minutes.`)},[]),(0,b.jsx)(p,{}))},T={render:()=>((0,y.useEffect)(()=>{v(`success`,`Product created`),v(`info`,`Syncing with supplier...`),v(`error`,`Failed to update inventory`)},[]),(0,b.jsx)(p,{}))},E={render:()=>{let e=e=>{v(e,{success:`Operation completed successfully!`,error:`Something went wrong. Please retry.`,info:`Here is some useful information.`}[e])};return(0,b.jsxs)(`div`,{className:`flex gap-2`,children:[(0,b.jsx)(f,{variant:`primary`,size:`sm`,onClick:()=>e(`success`),children:`Success`}),(0,b.jsx)(f,{variant:`danger`,size:`sm`,onClick:()=>e(`error`),children:`Error`}),(0,b.jsx)(f,{variant:`secondary`,size:`sm`,onClick:()=>e(`info`),children:`Info`}),(0,b.jsx)(p,{})]})}},S.parameters={...S.parameters,docs:{...S.parameters?.docs,source:{originalSource:`{
  render: () => {
    useEffect(() => {
      addToast('success', 'Product updated successfully');
    }, []);
    return <ToastContainer />;
  }
}`,...S.parameters?.docs?.source}}},C.parameters={...C.parameters,docs:{...C.parameters?.docs,source:{originalSource:`{
  render: () => {
    useEffect(() => {
      addToast('error', 'Failed to save changes. Please try again.');
    }, []);
    return <ToastContainer />;
  }
}`,...C.parameters?.docs?.source}}},w.parameters={...w.parameters,docs:{...w.parameters?.docs,source:{originalSource:`{
  render: () => {
    useEffect(() => {
      addToast('info', 'Your session will expire in 5 minutes.');
    }, []);
    return <ToastContainer />;
  }
}`,...w.parameters?.docs?.source}}},T.parameters={...T.parameters,docs:{...T.parameters?.docs,source:{originalSource:`{
  render: () => {
    useEffect(() => {
      addToast('success', 'Product created');
      addToast('info', 'Syncing with supplier...');
      addToast('error', 'Failed to update inventory');
    }, []);
    return <ToastContainer />;
  }
}`,...T.parameters?.docs?.source}}},E.parameters={...E.parameters,docs:{...E.parameters?.docs,source:{originalSource:`{
  render: () => {
    const add = (type: 'success' | 'error' | 'info') => {
      const messages = {
        success: 'Operation completed successfully!',
        error: 'Something went wrong. Please retry.',
        info: 'Here is some useful information.'
      };
      addToast(type, messages[type]);
    };
    return <div className="flex gap-2">
        <Button variant="primary" size="sm" onClick={() => add('success')}>Success</Button>
        <Button variant="danger" size="sm" onClick={() => add('error')}>Error</Button>
        <Button variant="secondary" size="sm" onClick={() => add('info')}>Info</Button>
        <ToastContainer />
      </div>;
  }
}`,...E.parameters?.docs?.source}}},D=[`Success`,`Error`,`Info`,`Stacked`,`Interactive`]}))();export{C as Error,w as Info,E as Interactive,T as Stacked,S as Success,D as __namedExportsOrder,x as default};