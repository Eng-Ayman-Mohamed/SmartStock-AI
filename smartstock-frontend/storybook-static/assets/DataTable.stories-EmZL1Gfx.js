import{i as e,s as t}from"./preload-helper-xPQekRTU.js";import{t as n}from"./react-CnPKFcMr.js";import{x as r}from"./iframe-DD82_D2a.js";import{Mt as i,P as a,St as o,bt as s,gt as c,mt as l,t as u,vt as d,wt as f}from"./lucide-react-BXoma8fF.js";import{n as p,t as m}from"./Button-U1y0I8Ib.js";import{n as h,t as g}from"./Badge-BgfJFn_W.js";import{n as _,t as v}from"./Skeleton-L7LT8FYh.js";import{n as y,t as b}from"./EmptyState-O_-7EDRq.js";function x({columns:e,data:t,keyExtractor:n,caption:r,emptyState:a,pagination:u,onSort:p,fillHeight:h=!0,actionsLabel:g,renderActions:_}){return t.length===0&&a?(0,C.jsx)(C.Fragment,{children:a}):(0,C.jsxs)(`div`,{className:h?`min-w-0 flex flex-col flex-1 min-h-0`:`min-w-0`,children:[(0,C.jsx)(`div`,{className:h?`overflow-auto flex-1 min-h-0`:`overflow-x-auto`,children:(0,C.jsxs)(`table`,{className:`w-full table-fixed border-collapse min-w-[480px]`,children:[r&&(0,C.jsx)(`caption`,{className:`sr-only`,children:r}),(0,C.jsx)(`thead`,{className:`sticky top-0 z-10`,children:(0,C.jsxs)(`tr`,{className:`bg-canvas-soft border-b border-hairline`,children:[e.map(e=>(0,C.jsx)(`th`,{scope:`col`,className:`h-12 px-3 text-body font-semibold text-ink-secondary select-none text-left`,style:e.width?{width:e.width}:void 0,children:e.sortable?(0,C.jsxs)(`button`,{type:`button`,onClick:()=>p?.(e.key),className:`inline-flex items-center gap-1 hover:text-ink transition-colors cursor-pointer`,children:[e.label,e.sortOrder===`asc`?(0,C.jsx)(d,{className:`w-3 h-3`}):e.sortOrder===`desc`?(0,C.jsx)(f,{className:`w-3 h-3`}):(0,C.jsx)(i,{className:`w-3 h-3 text-ink-faint`})]}):e.label},e.key)),g&&(0,C.jsx)(`th`,{className:`h-12 px-3 text-body font-semibold text-ink-secondary select-none text-center`,style:{width:`9%`},scope:`col`,children:g})]})}),(0,C.jsx)(`tbody`,{children:t.map(t=>(0,C.jsxs)(`tr`,{className:`bg-canvas border-b border-hairline hover:bg-canvas-soft transition-colors duration-150 group`,tabIndex:0,onKeyDown:e=>{if(e.key===`Enter`||e.key===` `){let t=e.currentTarget.querySelector(`button, a, [role="button"]`);t instanceof HTMLElement&&t.click()}},role:`row`,children:[e.map(e=>(0,C.jsx)(`td`,{className:`h-12 px-3 text-body text-ink-secondary truncate text-left`,children:e.render(t)},e.key)),_&&(0,C.jsx)(`td`,{className:`h-12 px-3 text-body text-ink-secondary text-left`,children:_(t)})]},n(t)))})]})}),u&&u.total>0&&(0,C.jsxs)(`div`,{className:`flex flex-col gap-3 border-t border-hairline px-4 py-3 sm:flex-row sm:items-center sm:justify-between`,children:[(0,C.jsxs)(`p`,{className:`text-caption text-ink-muted`,children:[`Showing`,` `,(0,C.jsx)(`span`,{className:`tabular-nums text-ink-secondary`,children:u.startItem}),` - `,(0,C.jsx)(`span`,{className:`tabular-nums text-ink-secondary`,children:u.endItem}),` of `,(0,C.jsx)(`span`,{className:`tabular-nums text-ink-secondary`,children:u.total}),u.itemLabel?(0,C.jsxs)(C.Fragment,{children:[` `,u.itemLabel]}):null]}),(0,C.jsxs)(`div`,{className:`flex items-center gap-1 overflow-x-auto`,"aria-label":`Pagination`,children:[(0,C.jsx)(m,{variant:`utility`,size:`sm`,className:`h-9 w-9 px-0 shrink-0 sm:h-11 sm:w-11`,onClick:()=>u.onPageChange(1),disabled:!u.hasPrev,"aria-label":`First page`,title:`First page`,children:(0,C.jsx)(c,{className:`h-4 w-4 sm:h-5 sm:w-5`})}),(0,C.jsx)(m,{variant:`utility`,size:`sm`,className:`h-9 w-9 px-0 shrink-0 sm:h-11 sm:w-11`,onClick:()=>u.onPageChange(Math.max(1,u.currentPage-1)),disabled:!u.hasPrev,"aria-label":`Previous page`,title:`Previous page`,children:(0,C.jsx)(o,{className:`h-4 w-4 sm:h-5 sm:w-5`})}),u.pages.map((e,t)=>e===-1?(0,C.jsx)(`span`,{className:`flex h-9 w-9 items-center justify-center text-caption text-ink-faint sm:h-11 sm:w-11`,children:`...`},`gap-${t}`):(0,C.jsx)(m,{variant:e===u.currentPage?`primary`:`utility`,size:`sm`,className:`h-9 w-9 px-0 tabular-nums shrink-0 sm:h-11 sm:w-11`,onClick:()=>u.onPageChange(e),"aria-label":`Page ${e}`,title:`Page ${e}`,children:e},e)),(0,C.jsx)(m,{variant:`utility`,size:`sm`,className:`h-9 w-9 px-0 shrink-0 sm:h-11 sm:w-11`,onClick:()=>u.onPageChange(Math.min(u.totalPages,u.currentPage+1)),disabled:!u.hasNext,"aria-label":`Next page`,title:`Next page`,children:(0,C.jsx)(s,{className:`h-4 w-4 sm:h-5 sm:w-5`})}),(0,C.jsx)(m,{variant:`utility`,size:`sm`,className:`h-9 w-9 px-0 shrink-0 sm:h-11 sm:w-11`,onClick:()=>u.onPageChange(u.totalPages),disabled:!u.hasNext,"aria-label":`Last page`,title:`Last page`,children:(0,C.jsx)(l,{className:`h-4 w-4 sm:h-5 sm:w-5`})})]})]})]})}var S,C,w,T=e((()=>{S=t(n(),1),u(),p(),C=r(),w=(0,S.memo)(x),x.__docgenInfo={description:``,methods:[],displayName:`DataTable`,props:{columns:{required:!0,tsType:{name:`Array`,elements:[{name:`Column`,elements:[{name:`T`}],raw:`Column<T>`}],raw:`Column<T>[]`},description:``},data:{required:!0,tsType:{name:`Array`,elements:[{name:`T`}],raw:`T[]`},description:``},keyExtractor:{required:!0,tsType:{name:`signature`,type:`function`,raw:`(row: T) => string`,signature:{arguments:[{type:{name:`T`},name:`row`}],return:{name:`string`}}},description:``},caption:{required:!1,tsType:{name:`string`},description:``},emptyState:{required:!1,tsType:{name:`ReactNode`},description:``},pagination:{required:!1,tsType:{name:`PaginationConfig`},description:``},onSort:{required:!1,tsType:{name:`signature`,type:`function`,raw:`(key: string) => void`,signature:{arguments:[{type:{name:`string`},name:`key`}],return:{name:`void`}}},description:``},fillHeight:{required:!1,tsType:{name:`boolean`},description:``,defaultValue:{value:`true`,computed:!1}},actionsLabel:{required:!1,tsType:{name:`string`},description:``},renderActions:{required:!1,tsType:{name:`signature`,type:`function`,raw:`(row: T) => ReactNode`,signature:{arguments:[{type:{name:`T`},name:`row`}],return:{name:`ReactNode`}}},description:``}}}})),E,D,O,k,A,j,M,N,P,F,I,L;e((()=>{E=t(n(),1),T(),h(),_(),y(),u(),D=r(),O=[{id:`1`,name:`Widget Alpha`,sku:`WID-001`,stock:142,status:`In Stock`},{id:`2`,name:`Widget Beta`,sku:`WID-002`,stock:8,status:`Low Stock`},{id:`3`,name:`Gadget Gamma`,sku:`GAD-001`,stock:0,status:`Out of Stock`},{id:`4`,name:`Gadget Delta`,sku:`GAD-002`,stock:56,status:`In Stock`},{id:`5`,name:`Component Epsilon`,sku:`CMP-001`,stock:234,status:`In Stock`},{id:`6`,name:`Component Zeta`,sku:`CMP-002`,stock:3,status:`Low Stock`},{id:`7`,name:`Tool Eta`,sku:`TOL-001`,stock:19,status:`In Stock`},{id:`8`,name:`Tool Theta`,sku:`TOL-002`,stock:0,status:`Out of Stock`}],k=[{key:`name`,label:`Product Name`,width:`30%`,render:e=>e.name,sortable:!0},{key:`sku`,label:`SKU`,width:`20%`,render:e=>e.sku,sortable:!0},{key:`stock`,label:`Stock`,width:`15%`,render:e=>e.stock.toLocaleString(),sortable:!0},{key:`status`,label:`Status`,width:`20%`,render:e=>(0,D.jsx)(g,{variant:e.status,children:e.status}),sortable:!0}],A=(0,D.jsx)(b,{icon:a,heading:`No products found`,body:`Try adjusting your search or filter criteria.`}),j={title:`Primitives/DataTable`,component:w,tags:[`autodocs`],args:{columns:k,keyExtractor:e=>e.id,caption:`Products table`}},M={args:{data:O}},N={args:{data:[],emptyState:A}},P={args:{data:[],emptyState:(0,D.jsx)(`div`,{className:`p-4`,children:(0,D.jsx)(v,{lines:6})})}},F={args:{data:O,pagination:{currentPage:1,totalPages:3,total:24,startItem:1,endItem:8,hasPrev:!1,hasNext:!0,pages:[1,2,3],onPageChange:e=>console.log(`Page:`,e),itemLabel:`products`}}},I={render:e=>{let[t,n]=(0,E.useState)(null),[r,i]=(0,E.useState)(`asc`),a=(0,E.useCallback)(e=>{n(t=>t===e?(i(e=>e===`asc`?`desc`:`asc`),e):(i(`asc`),e))},[]),o=k.map(e=>({...e,sortOrder:e.key===t?r:void 0,sortable:!0})),s=[...O].sort((e,n)=>{let i=e[t]?.toString()??``,a=n[t]?.toString()??``;return r===`asc`?i.localeCompare(a):a.localeCompare(i)});return(0,D.jsx)(w,{...e,columns:o,data:s,onSort:a})}},M.parameters={...M.parameters,docs:{...M.parameters?.docs,source:{originalSource:`{
  args: {
    data: sampleData
  }
}`,...M.parameters?.docs?.source}}},N.parameters={...N.parameters,docs:{...N.parameters?.docs,source:{originalSource:`{
  args: {
    data: [],
    emptyState
  }
}`,...N.parameters?.docs?.source}}},P.parameters={...P.parameters,docs:{...P.parameters?.docs,source:{originalSource:`{
  args: {
    data: [],
    emptyState: <div className="p-4">
        <Skeleton lines={6} />
      </div>
  }
}`,...P.parameters?.docs?.source}}},F.parameters={...F.parameters,docs:{...F.parameters?.docs,source:{originalSource:`{
  args: {
    data: sampleData,
    pagination: {
      currentPage: 1,
      totalPages: 3,
      total: 24,
      startItem: 1,
      endItem: 8,
      hasPrev: false,
      hasNext: true,
      pages: [1, 2, 3],
      onPageChange: page => console.log('Page:', page),
      itemLabel: 'products'
    }
  }
}`,...F.parameters?.docs?.source}}},I.parameters={...I.parameters,docs:{...I.parameters?.docs,source:{originalSource:`{
  render: args => {
    const [sortKey, setSortKey] = useState<string | null>(null);
    const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('asc');
    const handleSort = useCallback((key: string) => {
      setSortKey(prev => {
        if (prev === key) {
          setSortOrder(o => o === 'asc' ? 'desc' : 'asc');
          return key;
        }
        setSortOrder('asc');
        return key;
      });
    }, []);
    const sortedColumns = columns.map(col => ({
      ...col,
      sortOrder: col.key === sortKey ? sortOrder : undefined,
      sortable: true
    }));
    const sorted = [...sampleData].sort((a, b) => {
      const aVal = a[sortKey as keyof Product]?.toString() ?? '';
      const bVal = b[sortKey as keyof Product]?.toString() ?? '';
      return sortOrder === 'asc' ? aVal.localeCompare(bVal) : bVal.localeCompare(aVal);
    });
    return <DataTable {...args} columns={sortedColumns} data={sorted} onSort={handleSort} />;
  }
}`,...I.parameters?.docs?.source}}},L=[`Default`,`Empty`,`Loading`,`WithPagination`,`Sortable`]}))();export{M as Default,N as Empty,P as Loading,I as Sortable,F as WithPagination,L as __namedExportsOrder,j as default};