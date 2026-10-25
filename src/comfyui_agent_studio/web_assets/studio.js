"use strict";
const $ = (id) => document.getElementById(id);
const state = {jobs:[], workflows:[], definition:null, benchmark:{}, filter:"all", selected:null, reference:null, source:null};
const phase = {created:"准备中",submitted:"已提交",queued:"排队中",running:"生成中",completed:"已完成",failed:"失败已留存",cancelled:"已取消"};
const token = document.querySelector('meta[name="studio-token"]').content;
async function api(path, options={}) {
  const response = await fetch(path, {...options, headers:{"X-Studio-Token":token,...options.headers}});
  const value = await response.json();
  if (!response.ok) throw new Error(typeof value.detail === "string" ? value.detail : JSON.stringify(value.detail ?? value));
  return value;
}
function element(tag, cls, text) { const item=document.createElement(tag); if(cls)item.className=cls; if(text!==undefined)item.textContent=text; return item; }
function nameFor(job){return state.benchmark[job.benchmark_task_id]?.character || job.request.output_label || job.workflow_id;}
function visualFailed(job){return job.resolved_parameters.visual_acceptance === "failed" || (job.human_evaluation && job.human_evaluation.overall_1_to_5 <= 2);}
function selectPreview(job){
  if(!job.artifacts.length)return;
  state.selected=job; $("preview-empty").hidden=true; $("preview-image").hidden=false;
  $("preview-image").src=job.artifacts[0].url; $("preview-image").alt=nameFor(job);
  $("preview-title").textContent=nameFor(job); $("preview-workflow").textContent=job.workflow_id;
  $("preview-type").textContent=visualFailed(job)?"已保留 · 待改进":"本地生成作品";
  $("preview-size").textContent=job.workflow_id.includes("hq")?"2× 精修":"原始输出";
}
function openDetails(job, index=0){
  $("dialog-title").textContent=nameFor(job);
  $("dialog-image").hidden=!job.artifacts.length;
  if(job.artifacts.length)$("dialog-image").src=job.artifacts[index].url;
  $("dialog-image").alt=nameFor(job);
  $("dialog-path").value=job.artifacts[index]?.path||"此任务没有生成图片；记录已保留。";
  $("dialog-note").textContent=job.error_detail||job.human_evaluation?.notes||"本地创作记录。未自动选入公开作品集。";
  $("dialog-manifest").textContent=JSON.stringify(job,null,2);
  $("artifact-dialog").showModal();
}
function renderGallery(){
  $("gallery").replaceChildren(); let total=0;
  for(const job of state.jobs){
    const category=state.benchmark[job.benchmark_task_id]?.category;
    if(state.filter!=="all" && !(state.filter===category || state.filter===job.client || (state.filter==="failed"&&(job.status==="failed"||visualFailed(job))))) continue;
    const artifacts=job.artifacts.length?job.artifacts:[null];
    artifacts.forEach((artifact,index)=>{
      const card=element("button","art-card");card.type="button";
      card.setAttribute("aria-label",`查看${nameFor(job)} ${phase[job.status]}`);
      const art=element("div","card-art");
      if(artifact){const img=element("img");img.src=artifact.url;img.alt=nameFor(job);img.loading="lazy";art.append(img);}
      else art.append(element("span","failure",phase[job.status]+"\n"+(job.error_category||"运行记录")));
      art.append(element("span","card-client",job.client.toUpperCase()));
      const info=element("div","card-info");info.append(element("h3",null,nameFor(job)));
      const meta=element("div","card-meta");meta.append(element("span",null,job.workflow_id.replace(".v1","")),element("span",visualFailed(job)?"bad":"",visualFailed(job)?"视觉待改进":phase[job.status]));
      info.append(meta);card.append(art,info);card.onclick=()=>{selectPreview(job);openDetails(job,index);};$("gallery").append(card);total++;
    });
  }
  $("history-count").textContent=`/ ${state.jobs.length} 次创作`;
  $("history-empty").hidden=total>0;
}
async function refreshJobs(){
  state.jobs=await api("/api/jobs");renderGallery();
  if(!state.selected){const best=state.jobs.find(j=>j.benchmark_task_id==="ocean-astrology-priest")||state.jobs.find(j=>j.artifacts.length);if(best)selectPreview(best);}
}
async function health(){
  try{const data=await api("/api/health");$("connection").className="connection "+(data.connected?"online":"offline");
    const gpu=data.system?.devices?.[0];
    $("connection").querySelector("span").textContent=data.connected?`ComfyUI ${data.system.system.comfyui_version} · ${gpu?(gpu.vram_free/1073741824).toFixed(1)+" GB 可用":"已连接"}`:"未连接 · 请手动打开 Desktop";
  }catch(error){$("connection").className="connection offline";$("connection").querySelector("span").textContent="连接异常 · 点击刷新重试";}
}
async function changeWorkflow(){
  const d=await api("/api/workflows/"+encodeURIComponent($("workflow").value));state.definition=d;
  const modes={txt2img:"文字生成图片",upscale:"先生成，再进行 2× 精修",img2img:"参考图重绘 · 保持原构图",incontext:"参考身份生成 · 允许新构图"};
  $("workflow-hint").textContent=modes[d.mode];$("workflow-mode").textContent=d.mode.toUpperCase();
  $("reference-box").hidden=!["img2img","incontext"].includes(d.mode);
  for(const key of ["width","height","steps","cfg","denoise"]){$(key).disabled=!d.parameters[key];if(d.defaults[key]!==undefined)$(key).value=d.defaults[key];}
  $("negative").placeholder="留空使用工作流默认值";
}
function showJob(job){
  $("live-job").hidden=false;$("job-title").textContent=phase[job.status]||job.status;
  $("job-detail").textContent=job.error_detail||`${job.workflow_id} · Seed ${job.resolved_parameters.runs?.[0]?.seed ?? "待解析"} · ${job.job_id.slice(0,8)}`;
  const terminal=["completed","failed","cancelled"].includes(job.status);$("cancel-job").hidden=terminal;
  $("cancel-job").onclick=async()=>{try{showJob(await api(`/api/jobs/${job.job_id}/cancel`,{method:"POST"}));await refreshJobs();}catch(e){$("job-detail").textContent=e.message;}};
  if(job.status==="completed"&&job.artifacts.length)selectPreview(job);
}
$("compose").addEventListener("submit",async(event)=>{
  event.preventDefault();$("form-error").hidden=true;$("generate").disabled=true;
  try{
    if(!state.definition)throw Error("请先选择工作流");
    const d=state.definition;
    if(["img2img","incontext"].includes(d.mode)&&!state.reference)throw Error("请先上传一张角色参考图。");
    const seed=$("seed").value.trim();if(!/^-?\d+$/.test(seed)||BigInt(seed)<-1n||BigInt(seed)>18446744073709551615n)throw Error("Seed 需为 -1 或有效非负整数。");
    // Browser numbers cannot faithfully represent all uint64 seeds.
    if(BigInt(seed)>BigInt(Number.MAX_SAFE_INTEGER))throw Error("网页 Seed 最大支持 9007199254740991，更大的整数请使用 CLI。");
    const request={workflow_id:d.workflow_id,prompt:$("prompt").value,seed:Number(seed),count:Number($("count").value),client:"studio"};
    for(const key of ["width","height","steps","cfg","denoise"])if(d.parameters[key])request[key]=Number($(key).value);
    if($("negative").value.trim())request.negative_prompt=$("negative").value.trim();
    if(["img2img","incontext"].includes(d.mode))request.input_images=[state.reference.path];
    const job=await api("/api/jobs",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(request)});showJob(job);await refreshJobs();
    if(state.source)state.source.close();state.source=new EventSource(`/api/jobs/${job.job_id}/events`);
    state.source.addEventListener("job",async(event)=>{const update=JSON.parse(event.data);showJob(update);if(["completed","failed","cancelled"].includes(update.status)){state.source.close();await refreshJobs();await health();}});
    state.source.onerror=()=>{$("job-detail").textContent="状态连接暂时中断；任务会继续执行。可刷新记录查看结果。";};
  }catch(error){$("form-error").textContent=error.message;$("form-error").hidden=false;}
  finally{$("generate").disabled=false;}
});
$("reference").addEventListener("change",async()=>{state.reference=null;const file=$("reference").files[0];if(!file)return;$("reference-status").textContent="正在校验并上传…";try{const body=new FormData();body.append("file",file);state.reference=await api("/api/uploads",{method:"POST",body});$("reference-status").textContent=`已上传 · ${state.reference.width} × ${state.reference.height} · ${state.reference.sha256.slice(0,12)}`;}catch(error){$("reference-status").textContent=error.message;}});
$("example").onclick=()=>{$("prompt").value=state.definition?.workflow_id.startsWith("animagine")?"1girl, original character, adult woman, teal wavy hair, flowing ceremonial robes, coral staff, moonlit sea, starry sky, full body, masterpiece, high score, great score":"An original adult ocean astrologer, long wavy teal hair, layered ceremonial robes, coral staff and celestial map, standing beside a moonlit sea, elegant full body anime illustration, rich fabric details.";};
document.querySelectorAll("[data-filter]").forEach(button=>button.onclick=()=>{state.filter=button.dataset.filter;document.querySelectorAll("[data-filter]").forEach(b=>b.classList.toggle("selected",b===button));renderGallery();});
$("workflow").onchange=()=>changeWorkflow().catch(e=>{$("form-error").hidden=false;$("form-error").textContent=e.message;});
$("preview-open").onclick=()=>{if(state.selected)openDetails(state.selected);};
$("close-dialog").onclick=()=>{$("artifact-dialog").close();$("preview-open").focus({preventScroll:true});};
$("refresh").onclick=()=>Promise.all([refreshJobs(),health()]).catch(e=>{$("history-empty").hidden=false;$("history-empty").textContent=e.message;});
async function init(){
  try{const [workflows,benchmarks]=await Promise.all([api("/api/workflows"),api("/api/benchmarks")]);state.workflows=workflows;state.benchmark=Object.fromEntries(benchmarks.tasks.map(t=>[t.id,t]));$("workflow").replaceChildren();for(const d of workflows){const option=element("option",null,d.title);option.value=d.workflow_id;$("workflow").append(option);}await changeWorkflow();await refreshJobs();await health();}
  catch(error){$("form-error").hidden=false;$("form-error").textContent="工作台初始化失败："+error.message;}
}
init();setInterval(health,30000);
