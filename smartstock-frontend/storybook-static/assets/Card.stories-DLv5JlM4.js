import{i as e}from"./preload-helper-xPQekRTU.js";import{x as t}from"./iframe-DD82_D2a.js";import{n,t as r}from"./Button-U1y0I8Ib.js";import{n as i,t as a}from"./Card-BSJFiygr.js";var o,s,c,l,u,d,f,p;e((()=>{i(),n(),o=t(),s={title:`Primitives/Card`,component:a,tags:[`autodocs`],argTypes:{title:{control:`text`},subtitle:{control:`text`},noPadding:{control:`boolean`}},args:{children:`Card content goes here.`}},c={args:{title:`Card Title`,children:`This is a basic card with a title and content.`}},l={args:{title:`Card Title`,subtitle:`A brief description of this card section.`,children:`Card content with subtitle visible above.`}},u={args:{title:`Inventory Summary`,action:(0,o.jsx)(r,{size:`sm`,variant:`ghost`,children:`View All`}),children:`Card with an action button in the header.`}},d={args:{children:`A simple card without a title or header section.`}},f={args:{title:`Full-bleed Content`,noPadding:!0,children:(0,o.jsx)(`div`,{className:`p-4 sm:p-6`,children:`Content with no padding on the card body.`})}},c.parameters={...c.parameters,docs:{...c.parameters?.docs,source:{originalSource:`{
  args: {
    title: 'Card Title',
    children: 'This is a basic card with a title and content.'
  }
}`,...c.parameters?.docs?.source}}},l.parameters={...l.parameters,docs:{...l.parameters?.docs,source:{originalSource:`{
  args: {
    title: 'Card Title',
    subtitle: 'A brief description of this card section.',
    children: 'Card content with subtitle visible above.'
  }
}`,...l.parameters?.docs?.source}}},u.parameters={...u.parameters,docs:{...u.parameters?.docs,source:{originalSource:`{
  args: {
    title: 'Inventory Summary',
    action: <Button size="sm" variant="ghost">View All</Button>,
    children: 'Card with an action button in the header.'
  }
}`,...u.parameters?.docs?.source}}},d.parameters={...d.parameters,docs:{...d.parameters?.docs,source:{originalSource:`{
  args: {
    children: 'A simple card without a title or header section.'
  }
}`,...d.parameters?.docs?.source}}},f.parameters={...f.parameters,docs:{...f.parameters?.docs,source:{originalSource:`{
  args: {
    title: 'Full-bleed Content',
    noPadding: true,
    children: <div className="p-4 sm:p-6">
        Content with no padding on the card body.
      </div>
  }
}`,...f.parameters?.docs?.source}}},p=[`Default`,`WithSubtitle`,`WithAction`,`NoTitle`,`NoPadding`]}))();export{c as Default,f as NoPadding,d as NoTitle,u as WithAction,l as WithSubtitle,p as __namedExportsOrder,s as default};