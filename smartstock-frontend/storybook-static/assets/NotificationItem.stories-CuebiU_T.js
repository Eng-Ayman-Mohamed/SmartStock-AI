import{i as e}from"./preload-helper-xPQekRTU.js";import{c as t,s as n,x as r}from"./iframe-DD82_D2a.js";import{n as i,t as a}from"./NotificationItem-CZyMb-xs.js";var o,s,c,l,u,d,f,p,m;e((()=>{i(),n(),o=r(),s={id:1,type:`monitoring`,severity:`info`,title:`System health check passed`,message:`All systems are operating within normal parameters.`,metadata:{},is_read:!1,created_at:`2026-06-26T10:30:00Z`,updated_at:`2026-06-26T10:30:00Z`},c={title:`Notifications/NotificationItem`,component:a,tags:[`autodocs`],decorators:[e=>(t.setState({user:{id:1,email:`admin@smartstock.ai`,name:`Admin`,role:`admin`,is_active:!0},token:`mock-token`,isBootstrapping:!1}),(0,o.jsx)(e,{}))],args:{onClose:()=>{}}},l={args:{notification:{...s,severity:`info`,title:`Forecast updated`,message:`Demand forecast for Q3 has been updated with new data.`}}},u={args:{notification:{...s,severity:`warning`,title:`Low stock alert`,message:`Widget Alpha is running low. Current stock: 8 units.`,is_read:!1}}},d={args:{notification:{...s,severity:`critical`,title:`Stockout detected`,message:`Gadget Gamma is out of stock. Reorder immediately.`,is_read:!1}}},f={args:{notification:{...s,severity:`info`,title:`Report generated`,message:`Monthly inventory report has been generated successfully.`,is_read:!0}}},p={args:{notification:{...s,type:`escalation`,severity:`critical`,title:`Approval required`,message:`Purchase order #PO-2024-0421 requires your approval.`,is_read:!1}}},l.parameters={...l.parameters,docs:{...l.parameters?.docs,source:{originalSource:`{
  args: {
    notification: {
      ...mockNotification,
      severity: 'info',
      title: 'Forecast updated',
      message: 'Demand forecast for Q3 has been updated with new data.'
    }
  }
}`,...l.parameters?.docs?.source}}},u.parameters={...u.parameters,docs:{...u.parameters?.docs,source:{originalSource:`{
  args: {
    notification: {
      ...mockNotification,
      severity: 'warning',
      title: 'Low stock alert',
      message: 'Widget Alpha is running low. Current stock: 8 units.',
      is_read: false
    }
  }
}`,...u.parameters?.docs?.source}}},d.parameters={...d.parameters,docs:{...d.parameters?.docs,source:{originalSource:`{
  args: {
    notification: {
      ...mockNotification,
      severity: 'critical',
      title: 'Stockout detected',
      message: 'Gadget Gamma is out of stock. Reorder immediately.',
      is_read: false
    }
  }
}`,...d.parameters?.docs?.source}}},f.parameters={...f.parameters,docs:{...f.parameters?.docs,source:{originalSource:`{
  args: {
    notification: {
      ...mockNotification,
      severity: 'info',
      title: 'Report generated',
      message: 'Monthly inventory report has been generated successfully.',
      is_read: true
    }
  }
}`,...f.parameters?.docs?.source}}},p.parameters={...p.parameters,docs:{...p.parameters?.docs,source:{originalSource:`{
  args: {
    notification: {
      ...mockNotification,
      type: 'escalation',
      severity: 'critical',
      title: 'Approval required',
      message: 'Purchase order #PO-2024-0421 requires your approval.',
      is_read: false
    }
  }
}`,...p.parameters?.docs?.source}}},m=[`InfoUnread`,`WarningUnread`,`CriticalUnread`,`Read`,`Escalation`]}))();export{d as CriticalUnread,p as Escalation,l as InfoUnread,f as Read,u as WarningUnread,m as __namedExportsOrder,c as default};