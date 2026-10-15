/* RIFTWARD: ECLIPSE — original offline roguelite. Copyright (c) 2026. */
(()=>{'use strict';
const $=id=>document.getElementById(id),canvas=$('world'),ctx=canvas.getContext('2d',{alpha:false});
const UI={menu:$('menu'),hud:$('hud'),controls:$('controls'),upgrade:$('upgrade'),pause:$('pause'),gameover:$('gameover'),settings:$('settings'),shards:$('shards'),hpNum:$('hpNum'),hpBar:$('hpBar'),waveDisplay:$('waveDisplay'),waveTime:$('waveTime'),waveProgress:$('waveProgress'),phaseText:$('phaseText'),bossPanel:$('bossBarPanel'),bossBar:$('bossBar'),bossPct:$('bossPct'),novaBtn:$('novaBtn'),novaLabel:$('novaLabel'),novaFill:$('novaFill'),joyArea:$('joyArea'),joyStick:$('joyStick'),toast:$('toast'),warning:$('warning'),fps:$('fps'),best:$('menuBest'),kills:$('menuKills')};
const TAU=Math.PI*2,COL={teal:'#75fce3',mint:'#b4fff2',gold:'#ffbe79',violet:'#aa8dff',coral:'#fd8799',ink:'#060b20',blue:'#77aaf6'};
const saveKey='riftward-eclipse-record-v1',settingsKey='riftward-eclipse-settings-v1';
const load=(key,defaultValue)=>{try{const v=JSON.parse(localStorage.getItem(key));return v&&typeof v==='object'?v:defaultValue}catch(_){return defaultValue}};
const record=Object.assign({wave:0,kills:0,shards:0,runs:0},load(saveKey,{}));
const options=Object.assign({sound:false,effects:true,haptics:true,fps:false,quality:'AUTO'},load(settingsKey,{}));
const keep=()=>{try{localStorage.setItem(saveKey,JSON.stringify(record));localStorage.setItem(settingsKey,JSON.stringify(options))}catch(_){}};
let W=390,H=844,DPR=1,last=0,ambient=0,frame=0,measuredFps=60,frames=0,fpsTime=0,fxScale=1;
let mode='menu',previousMode='menu',wave=1,waveClock=0,elapsed=0,spawnClock=0,bossSpawned=false,boss=null,warningClock=0,toaster=0,shake=0,flash=0,upgradeSet=[],motion={x:0,y:0},pointerId=null,keyDirections={};
let hero={x:0,y:0,r:15,hp:100,maxHp:100,shield:0,move:208,speed:1,damage:20,fireInterval:.49,projectileSpeed:520,projectileSize:4.5,multishot:1,pierce:0,crit:.06,magnet:72,novaPower:78,novaCooldown:14,novaTimer:0,novaRadius:178,regen:0,armor:0,orbit:0,orbitDamage:18,invuln:0,angle:0,shotTimer:0,level:1};
let enemies=[],shots=[],hostileShots=[],particles=[],pickups=[],floaters=[],sparks=[],afterimages=[],enemySeq=0,kills=0,shards=0,orbAngle=0,afterClock=0;
let audio=null,master=null;
const clamp=(n,a,b)=>Math.max(a,Math.min(b,n));
const lerp=(a,b,t)=>a+(b-a)*t;
const rand=(a,b)=>a+Math.random()*(b-a);
const dist2=(ax,ay,bx,by)=>(ax-bx)**2+(ay-by)**2;
const hash=(x,y,k=13)=>{let n=Math.imul(x+61483,374761393)+Math.imul(y+789221,668265263)+Math.imul(k+79,362437);n=(n^(n>>>13));n=Math.imul(n,1274126177);return ((n^(n>>>16))>>>0)/4294967295};
const vis=(id,yes)=>$(id).classList.toggle('hidden',!yes);
const logState=(state=mode)=>console.log('RIFTWARD_STATE: '+state);
const haptic=n=>{if(options.haptics&&navigator.vibrate)try{navigator.vibrate(n)}catch(_){}};
function tone(freq=300,seconds=.08,kind='sine',gain=.045,slide=1){if(!options.sound)return;try{if(!audio){audio=new(window.AudioContext||window.webkitAudioContext)();master=audio.createGain();master.gain.value=.55;master.connect(audio.destination)}if(audio.state==='suspended')audio.resume();const o=audio.createOscillator(),g=audio.createGain(),now=audio.currentTime;o.type=kind;o.frequency.setValueAtTime(freq,now);o.frequency.exponentialRampToValueAtTime(Math.max(30,freq*slide),now+seconds);g.gain.setValueAtTime(gain,now);g.gain.exponentialRampToValueAtTime(.0002,now+seconds);o.connect(g);g.connect(master);o.start(now);o.stop(now+seconds+.01)}catch(_){}}
function storeOptions(){keep();['Sound','Effects','Haptics','Fps'].forEach(p=>{let el=$('toggle'+p),on=options[p.toLowerCase()];el.textContent=on?'ON':'OFF';el.classList.toggle('off',!on)});$('toggleQuality').textContent=options.quality;document.documentElement.classList.toggle('fx-off',!options.effects);vis('fps',options.fps);resize()}
function resize(){let bounds=canvas.getBoundingClientRect();W=Math.max(280,bounds.width||innerWidth);H=Math.max(430,bounds.height||innerHeight);let quality=options.quality==='HIGH'?2:options.quality==='ECO'?1:Math.min(window.devicePixelRatio||1,1.65);DPR=clamp(quality*fxScale,.8,2);canvas.width=Math.round(W*DPR);canvas.height=Math.round(H*DPR);ctx.setTransform(DPR,0,0,DPR,0,0)}
function showToast(message){UI.toast.textContent=message;vis('toast',true);toaster=2.3;UI.toast.style.animation='none';void UI.toast.offsetWidth;UI.toast.style.animation='toastPop 2.5s ease both'}
function showWarning(message){UI.warning.textContent=message;vis('warning',true);warningClock=2.8;haptic([45,40,45]);tone(180,.35,'sawtooth',.1,.55)}
function showScreen(next){mode=next;for(const id of ['menu','upgrade','pause','gameover','settings'])vis(id,id===(next==='paused'?'pause':next));vis('hud',next==='playing'||next==='paused'||next==='upgrade');vis('controls',next==='playing');UI.joyStick.style.transform='translate(-50%,-50%)';if(next!=='playing'){motion.x=motion.y=0;pointerId=null}logState()}
function openSettings(){previousMode=mode;showScreen('settings');storeOptions()}
function closeSettings(){showScreen(previousMode==='playing'?'paused':previousMode)}
function resetHero(){hero={x:0,y:0,r:15,hp:100,maxHp:100,shield:0,move:208,speed:1,damage:20,fireInterval:.49,projectileSpeed:520,projectileSize:4.5,multishot:1,pierce:0,crit:.06,magnet:72,novaPower:78,novaCooldown:14,novaTimer:0,novaRadius:178,regen:0,armor:0,orbit:0,orbitDamage:18,invuln:0,angle:0,shotTimer:0,level:1};}
function resetRun(){resetHero();enemies=[];shots=[];hostileShots=[];pickups=[];particles=[];floaters=[];afterimages=[];afterClock=0;enemySeq=0;kills=0;shards=0;wave=1;waveClock=0;elapsed=0;spawnClock=0;bossSpawned=false;boss=null;shake=0;flash=0;warningClock=0;upgradeSet=[];record.runs++;keep();UI.bossPanel.classList.add('hidden');updateHud();showScreen('playing');showToast('WARDEN ONLINE');tone(660,.12,'triangle');}
function openMenu(){if(mode==='playing'||mode==='paused')commitRecord();showScreen('menu');UI.best.textContent='WAVE '+String(record.wave).padStart(2,'0');UI.kills.textContent=String(record.kills).padStart(4,'0');UI.bossPanel.classList.add('hidden')}
function pauseGame(){if(mode!=='playing')return;showScreen('paused');tone(290,.11,'triangle')}
function resume(){if(mode!=='paused')return;showScreen('playing');last=0;tone(470,.09,'triangle')}
function commitRecord(){record.wave=Math.max(record.wave,wave);record.kills=Math.max(record.kills,kills);record.shards=Math.max(record.shards,shards);keep()}
function defeat(){if(mode!=='playing')return;hero.hp=0;commitRecord();$('endWave').textContent=String(wave).padStart(2,'0');$('endKills').textContent=String(kills).padStart(3,'0');$('endTime').textContent=formatTime(elapsed);flash=.8;shake=10;tone(280,.4,'sawtooth',.095,.3);showScreen('gameover');haptic([90,55,100]);}
function formatTime(sec){const n=Math.floor(sec);return String((n/60)|0).padStart(2,'0')+':'+String(n%60).padStart(2,'0')}
const UPGRADE_POOL=[
{id:'blaze',title:'SOLAR LANCE',icon:'✷',tier:'OFFENSIVE',desc:'Primary bolts deal +30% damage.',apply(){hero.damage*=1.3}},
{id:'cadence',title:'RAPID CONVERGENCE',icon:'⌁',tier:'OFFENSIVE',desc:'Fire 20% faster.',apply(){hero.fireInterval*=.8}},
{id:'twin',title:'TWIN COMETS',icon:'☷',tier:'EXOTIC',desc:'Fire an additional bolt per volley.',apply(){hero.multishot=Math.min(5,hero.multishot+1)}},
{id:'pierce',title:'PHASE PENETRATOR',icon:'◇',tier:'EXOTIC',desc:'Projectiles pierce one more enemy.',apply(){hero.pierce=Math.min(4,hero.pierce+1)}},
{id:'overdrive',title:'HELIOS ENGINE',icon:'➤',tier:'MOBILITY',desc:'Move 15% faster.',apply(){hero.move*=1.15}},
{id:'vitality',title:'AETHER ARMOR',icon:'♢',tier:'DEFENSIVE',desc:'+35 maximum hull and repair 35.',apply(){hero.maxHp+=35;hero.hp=Math.min(hero.maxHp,hero.hp+35)}},
{id:'repair',title:'PHOENIX SEAL',icon:'♥',tier:'DEFENSIVE',desc:'Repair 45 hull and gain +1 regen.',apply(){hero.hp=Math.min(hero.maxHp,hero.hp+45);hero.regen+=1}},
{id:'shield',title:'STARSHIELD',icon:'⬡',tier:'DEFENSIVE',desc:'Absorb 45 damage every wave.',apply(){hero.shield+=45}},
{id:'pulse',title:'NOVA STARBURST',icon:'✺',tier:'EXOTIC',desc:'NOVA deals +35% damage.',apply(){hero.novaPower*=1.35}},
{id:'reactor',title:'QUANTUM REACTOR',icon:'◈',tier:'EXOTIC',desc:'NOVA recharges 20% faster.',apply(){hero.novaCooldown*=.8}},
{id:'orbit',title:'ORBITAL GLAIVE',icon:'⟳',tier:'LEGENDARY',desc:'Summon a damaging orbital blade.',apply(){hero.orbit=Math.min(4,hero.orbit+1)}},
{id:'magnet',title:'GRAVITIC FIELD',icon:'◎',tier:'UTILITY',desc:'Collect shards from farther away.',apply(){hero.magnet+=65}},
{id:'crit',title:'CRITICAL FREQUENCY',icon:'✧',tier:'OFFENSIVE',desc:'+13% critical chance.',apply(){hero.crit=Math.min(.65,hero.crit+.13)}},
{id:'durability',title:'VOID RESISTANCE',icon:'⬟',tier:'DEFENSIVE',desc:'Reduce incoming damage by 15%.',apply(){hero.armor=Math.min(.65,hero.armor+.15)}}
];
function chooseUpgrades(){let pool=UPGRADE_POOL.filter(p=>p.id!=='twin'||hero.multishot<5).filter(p=>p.id!=='orbit'||hero.orbit<4),choices=[];while(choices.length<3&&pool.length){const i=Math.floor(Math.random()*pool.length);choices.push(pool.splice(i,1)[0])}upgradeSet=choices;UI.bossPanel.classList.add('hidden');$('upgradeCards').innerHTML='';for(const item of choices){const card=document.createElement('button');card.className='upgradeCard'+(item.tier==='LEGENDARY'||item.tier==='EXOTIC'?' gold':'');card.innerHTML=`<div class="upgradeIcon">${item.icon}</div><div class="upgradeInfo"><small>${item.tier}</small><b>${item.title}</b><span>${item.desc}</span></div>`;card.addEventListener('click',()=>applyUpgrade(item));$('upgradeCards').append(card)}showScreen('upgrade');tone(700,.16,'triangle');}
function applyUpgrade(item){if(mode!=='upgrade')return;item.apply();hero.level++;hero.shield=Math.min(hero.shield,140);wave++;waveClock=0;spawnClock=0;bossSpawned=false;boss=null;shots=[];hostileShots=[];enemies=[];pickups=[];hero.hp=clamp(hero.hp+Math.min(12,hero.maxHp-hero.hp),0,hero.maxHp);hero.shield+=Math.min(20,hero.maxHp*.2);showScreen('playing');showToast(item.title+' EQUIPPED');tone(860,.15,'sine');haptic(25);updateHud();}
function finishWave(){if(mode!=='playing')return;for(const e of enemies){for(let i=0;i<3;i++)spawnParticle(e.x,e.y,COL.gold,rand(-110,110),rand(-100,100),.35)}enemies=[];hostileShots=[];shots=[];chooseUpgrades();}
function spawnEnemy(type){const a=rand(0,TAU),rad=Math.min(W,H)*.68+rand(40,105);let e={id:++enemySeq,type,x:hero.x+Math.cos(a)*rad,y:hero.y+Math.sin(a)*rad,r:13,hp:30,maxHp:30,speed:75,touch:10,cd:rand(.2,1.5),anim:rand(0,TAU),hitFlash:0,split:false,elite:false};
 if(type==='skitter'){Object.assign(e,{r:10,hp:23,maxHp:23,speed:113,touch:8})}
 if(type==='prism'){Object.assign(e,{r:17,hp:65,maxHp:65,speed:31,touch:12,cd:rand(1,2)})}
 if(type==='bulwark'){Object.assign(e,{r:23,hp:125,maxHp:125,speed:36,touch:19,cd:2.1})}
 if(type==='boss'){Object.assign(e,{r:54,hp:480+wave*55,maxHp:480+wave*55,speed:34,touch:28,cd:1.5});boss=e}
 const mult=1+(wave-1)*.17;e.hp*=mult;e.maxHp*=mult;e.touch=Math.round(e.touch*(1+(wave-1)*.055));enemies.push(e);return e;
}
function spawnParticle(x,y,color,vx=rand(-95,95),vy=rand(-95,95),life=rand(.25,.75),size=rand(1.2,3.7)){if(!options.effects||particles.length>185)return;particles.push({x,y,color,vx,vy,life,max:life,size})}
function emitBurst(x,y,color,count=11){if(!options.effects)return;for(let i=0;i<count;i++){let a=i/Math.max(1,count)*TAU+rand(-.22,.22),sp=rand(50,185);spawnParticle(x,y,color,Math.cos(a)*sp,Math.sin(a)*sp,rand(.28,.72),rand(2,4.5))}}
function floating(x,y,label,color=COL.gold){if(floaters.length>20)floaters.shift();floaters.push({x,y,label,color,life:1,max:1})}
function hurtEnemy(e,raw,critical=false){if(e.hp<=0)return;e.hp-=raw;e.hitFlash=.13;floating(e.x+rand(-10,10),e.y-12,Math.ceil(raw)+(critical?'!':''),critical?COL.gold:COL.mint);if(e.hp<=0){kills++;shards+=e.type==='boss'?75:e.type==='bulwark'?7:e.type==='prism'?4:2;emitBurst(e.x,e.y,e.type==='boss'?COL.gold:COL.teal,e.type==='boss'?65:12);shake=Math.min(14,shake+(e.type==='boss'?8:1.2));if(e.type==='boss'){boss=null;showToast('SENTINEL SHATTERED');tone(850,.4,'triangle',.09,.6);haptic(80)}else tone(360,.035,'triangle',.015,1.5);if(Math.random()<.18||e.type==='boss')pickups.push({x:e.x,y:e.y,r:e.type==='boss'?12:7,value:e.type==='boss'?30:8,age:0});}
}
function hitHero(raw){if(hero.invuln>0||mode!=='playing')return;let incoming=raw*(1-hero.armor);const blocked=Math.min(hero.shield,incoming);hero.shield-=blocked;incoming-=blocked;hero.hp-=incoming;hero.invuln=.65;shake=7;flash=.33;emitBurst(hero.x,hero.y,COL.coral,14);floating(hero.x,hero.y-28,'-'+Math.round(incoming),COL.coral);tone(160,.14,'sawtooth',.04,.5);haptic(35);if(hero.hp<=0)defeat()}
function autoShoot(dt){hero.shotTimer-=dt;if(hero.shotTimer>0)return;let target=null,d=500**2;for(const e of enemies){if(e.hp<=0)continue;const nd=dist2(hero.x,hero.y,e.x,e.y);if(nd<d){d=nd;target=e}}if(!target)return;hero.shotTimer=Math.max(.12,hero.fireInterval);const aim=Math.atan2(target.y-hero.y,target.x-hero.x);hero.angle=aim;for(let i=0;i<hero.multishot;i++){let spread=(i-(hero.multishot-1)/2)*.18,a=aim+spread,crit=Math.random()<hero.crit;shots.push({x:hero.x+Math.cos(a)*16,y:hero.y+Math.sin(a)*16,vx:Math.cos(a)*hero.projectileSpeed,vy:Math.sin(a)*hero.projectileSpeed,r:hero.projectileSize+(crit?1.5:0),damage:hero.damage*(crit?1.75:1),pierce:hero.pierce,life:1.3,crit,trail:[]})}tone(510,.035,'sine',.018,.8);if(options.effects)spawnParticle(hero.x-Math.cos(aim)*13,hero.y-Math.sin(aim)*13,COL.gold,-Math.cos(aim)*65,-Math.sin(aim)*65,.16,3)}
function activateNova(){if(mode!=='playing'||hero.novaTimer>0)return false;hero.novaTimer=hero.novaCooldown;shake=9;flash=.28;emitBurst(hero.x,hero.y,COL.gold,55);sparks.push({x:hero.x,y:hero.y,r:5,max:hero.novaRadius,life:.63,maxLife:.63,color:COL.gold});for(const e of enemies)if(dist2(hero.x,hero.y,e.x,e.y)<(hero.novaRadius+e.r)**2)hurtEnemy(e,hero.novaPower);hostileShots=hostileShots.filter(b=>dist2(b.x,b.y,hero.x,hero.y)>hero.novaRadius**2);tone(130,.65,'sawtooth',.095,5);haptic([65,25,30]);return true}
function updateHud(){UI.hpBar.style.width=(clamp(hero.hp/hero.maxHp,0,1)*100)+'%';UI.hpBar.style.background=hero.hp/hero.maxHp<.3?'linear-gradient(90deg,#d94d73,#ffb089)':'linear-gradient(90deg,#35dcc1,#a8ffe4)';UI.hpNum.textContent=Math.max(0,Math.ceil(hero.hp))+' / '+hero.maxHp+(hero.shield>0?'  +' + Math.ceil(hero.shield):'');UI.waveDisplay.textContent=String(wave).padStart(2,'0');UI.shards.textContent=String(shards).padStart(3,'0');UI.waveTime.textContent=hero.hp<=0?'--:--':formatTime(Math.max(0,25-waveClock));UI.waveProgress.style.width=(clamp(waveClock/25,0,1)*100)+'%';UI.phaseText.textContent=boss&&boss.hp>0?'DEFEAT THE SENTINEL':waveClock<25?'SURVIVE THE SWARM':'FINAL SWEEP';const pct=hero.novaTimer<=0?100:clamp((1-hero.novaTimer/hero.novaCooldown)*100,0,100);UI.novaFill.style.height=pct+'%';UI.novaBtn.disabled=hero.novaTimer>0;UI.novaLabel.textContent=hero.novaTimer>0?Math.ceil(hero.novaTimer)+' SEC':'NOVA READY';vis('bossBarPanel',!!boss&&boss.hp>0);if(boss&&boss.hp>0){const p=clamp(boss.hp/boss.maxHp,0,1);UI.bossBar.style.width=(p*100)+'%';UI.bossPct.textContent=Math.ceil(p*100)+'%'}}
function runStep(dt){elapsed+=dt;waveClock+=dt;orbAngle+=dt*2;hero.novaTimer=Math.max(0,hero.novaTimer-dt);hero.invuln=Math.max(0,hero.invuln-dt);hero.hp=Math.min(hero.maxHp,hero.hp+hero.regen*dt);spawnClock-=dt;
 const dx=motion.x+(keyDirections.d?1:0)-(keyDirections.a?1:0)+(keyDirections.right?1:0)-(keyDirections.left?1:0);
 const dy=motion.y+(keyDirections.s?1:0)-(keyDirections.w?1:0)+(keyDirections.down?1:0)-(keyDirections.up?1:0);
 const len=Math.hypot(dx,dy);if(len>.01){hero.x+=(dx/Math.max(len,1))*hero.move*dt;hero.y+=(dy/Math.max(len,1))*hero.move*dt;hero.angle=Math.atan2(dy,dx);afterClock-=dt;if(afterClock<=0&&options.effects){afterimages.push({x:hero.x,y:hero.y,a:hero.angle,life:.28});if(afterimages.length>9)afterimages.shift();afterClock=.075}if(options.effects&&Math.random()<dt*18)spawnParticle(hero.x-Math.cos(hero.angle)*14,hero.y-Math.sin(hero.angle)*14,COL.teal,rand(-55,55),rand(-55,55),rand(.24,.6),rand(1,3))}
 let cap=Math.min(70,18+wave*7);if(spawnClock<=0&&enemies.length<cap&&waveClock<25){let t=Math.random(),type='wisp';if(wave>=2&&t<.3)type='skitter';if(wave>=3&&t>.75)type='prism';if(wave>=4&&t>.88)type='bulwark';spawnEnemy(type);spawnClock=clamp(1.3-wave*.10,.27,1.3)*rand(.7,1.25)}
 if(wave>=4&&wave%4===0&&!bossSpawned&&waveClock>=9){bossSpawned=true;spawnEnemy('boss');showWarning('ECLIPSE SENTINEL INBOUND')}
 for(const e of enemies){if(e.hp<=0)continue;e.anim+=dt*3.2;e.hitFlash=Math.max(0,e.hitFlash-dt);e.cd-=dt;const dx=hero.x-e.x,dy=hero.y-e.y,d=Math.max(1,Math.hypot(dx,dy)),ux=dx/d,uy=dy/d;if(e.type==='prism'&&d<235){e.x-=ux*e.speed*.4*dt;e.y-=uy*e.speed*.4*dt}else{e.x+=ux*e.speed*dt;e.y+=uy*e.speed*dt}
 if(e.type==='skitter'){e.x+=-uy*Math.sin(e.anim*1.3)*20*dt;e.y+=ux*Math.sin(e.anim*1.3)*20*dt}
 if(d<e.r+hero.r+4)hitHero(e.touch);
 if(e.type==='prism'&&e.cd<=0){e.cd=2.5-rand(0,.4);for(const offset of [-.11,0,.11]){let a=Math.atan2(dy,dx)+offset;hostileShots.push({x:e.x,y:e.y,vx:Math.cos(a)*135,vy:Math.sin(a)*135,r:4,life:4.2,color:COL.violet,damage:10})}emitBurst(e.x,e.y,COL.violet,5)}
 if(e.type==='boss'&&e.cd<=0){e.cd=2.4;if(d<280){for(let k=0;k<10;k++){const a=(k/10)*TAU+e.anim;hostileShots.push({x:e.x,y:e.y,vx:Math.cos(a)*115,vy:Math.sin(a)*115,r:6,life:4.5,color:COL.coral,damage:12})}}else{for(let k=-2;k<=2;k++){let a=Math.atan2(dy,dx)+k*.19;hostileShots.push({x:e.x,y:e.y,vx:Math.cos(a)*155,vy:Math.sin(a)*155,r:6,life:4,color:COL.coral,damage:14})}}showWarning('SENTINEL ENERGY SURGE')}
 }
 autoShoot(dt);
 for(const b of shots){b.life-=dt;b.x+=b.vx*dt;b.y+=b.vy*dt;for(const e of enemies){if(e.hp<=0||b.life<=0)continue;const radius=b.r+e.r;if(dist2(b.x,b.y,e.x,e.y)<radius*radius){hurtEnemy(e,b.damage,b.crit);b.pierce--;if(b.pierce<0)b.life=0;else{b.x+=b.vx*dt*2;b.y+=b.vy*dt*2}if(options.effects)emitBurst(b.x,b.y,b.crit?COL.gold:COL.teal,4)}}}shots=shots.filter(b=>b.life>0);
 for(const b of hostileShots){b.life-=dt;b.x+=b.vx*dt;b.y+=b.vy*dt;if(dist2(b.x,b.y,hero.x,hero.y)<(hero.r+b.r)**2){hitHero(b.damage);b.life=0}}hostileShots=hostileShots.filter(b=>b.life>0);
 if(hero.orbit){for(let k=0;k<hero.orbit;k++){const a=orbAngle+k*TAU/hero.orbit,x=hero.x+Math.cos(a)*77,y=hero.y+Math.sin(a)*77;for(const e of enemies){if(e.hp<=0)continue;if(dist2(x,y,e.x,e.y)<(11+e.r)**2){if(!e.orbitHits)e.orbitHits=0;if(elapsed-e.orbitHits>.35){e.orbitHits=elapsed;hurtEnemy(e,hero.orbitDamage)}}}}}
 for(const p of pickups){p.age+=dt;let dx=hero.x-p.x,dy=hero.y-p.y,d=Math.hypot(dx,dy);if(d<hero.magnet+110&&d>1){const sp=d<hero.magnet?420:180;p.x+=dx/d*sp*dt;p.y+=dy/d*sp*dt}if(d<hero.r+p.r+4){hero.shield=Math.min(100,hero.shield+p.value*.15);shards+=p.value;p.age=999;tone(660,.05,'sine',.025);if(options.effects)emitBurst(p.x,p.y,COL.gold,6)}}pickups=pickups.filter(p=>p.age<999&&p.age<20);
 enemies=enemies.filter(e=>e.hp>0);if(waveClock>=25&&(!boss||boss.hp<=0)){finishWave();return}
}
function simulation(dt){ambient+=dt;frame++;if(toaster>0){toaster-=dt;if(toaster<=0)vis('toast',false)}if(warningClock>0){warningClock-=dt;if(warningClock<=0)vis('warning',false)}shake=Math.max(0,shake-26*dt);flash=Math.max(0,flash-1.2*dt);for(const p of particles){p.life-=dt;p.x+=p.vx*dt;p.y+=p.vy*dt;p.vx*=.98;p.vy*=.98}particles=particles.filter(p=>p.life>0);for(const ghost of afterimages)ghost.life-=dt;afterimages=afterimages.filter(g=>g.life>0);for(const f of floaters){f.life-=dt;f.y-=27*dt}floaters=floaters.filter(f=>f.life>0);for(const s of sparks){s.life-=dt}sparks=sparks.filter(s=>s.life>0);if(mode==='playing')runStep(dt)}
function screenPos(x,y){return{x:W*.5+x-hero.x,y:H*.51+y-hero.y}}
function line(x1,y1,x2,y2,color,width=1){ctx.beginPath();ctx.moveTo(x1,y1);ctx.lineTo(x2,y2);ctx.strokeStyle=color;ctx.lineWidth=width;ctx.stroke()}
function ring(x,y,r,color,width=1){ctx.beginPath();ctx.arc(x,y,r,0,TAU);ctx.strokeStyle=color;ctx.lineWidth=width;ctx.stroke()}
function polygon(cx,cy,r,sides,angle=0){ctx.beginPath();for(let i=0;i<sides;i++){let a=angle+TAU*i/sides,x=cx+Math.cos(a)*r,y=cy+Math.sin(a)*r;i?ctx.lineTo(x,y):ctx.moveTo(x,y)}ctx.closePath()}
function background(){const grad=ctx.createLinearGradient(0,0,W,H);grad.addColorStop(0,'#050b20');grad.addColorStop(.53,'#080b1d');grad.addColorStop(1,'#190d25');ctx.fillStyle=grad;ctx.fillRect(0,0,W,H);
 let cx=mode==='menu'?ambient*13:hero.x,cy=mode==='menu'?ambient*9:hero.y;
 if(options.effects){const nebula=[{x:.12,y:.22,c:'#483b9142',r:.83},{x:.81,y:.72,c:'#285e6549',r:.66},{x:.48,y:.49,c:'#a9693e22',r:.62}];for(const n of nebula){let px=W*n.x+Math.sin(ambient*.13+n.x*5)*32,py=H*n.y+Math.cos(ambient*.12+n.y)*27,r=Math.max(W,H)*n.r,g=ctx.createRadialGradient(px,py,3,px,py,r);g.addColorStop(0,n.c);g.addColorStop(1,'#00000000');ctx.fillStyle=g;ctx.fillRect(px-r,py-r,2*r,2*r)}}
 // Aperiodic camera-space tiles: no texture-reset seam, ever.
 const sz=83,offx=((cx*.32%sz)+sz)%sz,offy=((cy*.32%sz)+sz)%sz;
 ctx.save();ctx.strokeStyle='#467c8550';ctx.lineWidth=.7;ctx.globalAlpha=.21;
 for(let x=-sz+offx;x<W+sz;x+=sz)line(x,0,x,H,'#527a9566',.75);
 for(let y=-sz+offy;y<H+sz;y+=sz)line(0,y,W,y,'#527a9566',.75);
 ctx.restore();
 const tile=112,tx0=Math.floor((cx*.11-W*.5)/tile),ty0=Math.floor((cy*.11-H*.51)/tile),maxX=Math.ceil(W/tile)+3,maxY=Math.ceil(H/tile)+3;
 for(let ty=ty0;ty<=ty0+maxY;ty++)for(let tx=tx0;tx<=tx0+maxX;tx++){
 const h=hash(tx,ty);if(h<.12)continue;const x=tx*tile-cx*.11+W*.5+hash(tx,ty,7)*90,y=ty*tile-cy*.11+H*.51+hash(tx,ty,2)*85;
 const alpha=.21+hash(tx,ty,9)*.58;ctx.globalAlpha=alpha*(.75+.25*Math.sin(ambient*.75+h*14));ctx.fillStyle=h>.8?'#fbbf9f':'#b7fff7';ctx.fillRect(x,y,h>.9?2:1.2,h>.9?2:1.2);
 if(options.effects&&h>.95){ctx.strokeStyle='#dbbeff55';ctx.lineWidth=.5;ctx.beginPath();ctx.moveTo(x-5,y);ctx.lineTo(x+5,y);ctx.moveTo(x,y-5);ctx.lineTo(x,y+5);ctx.stroke()}
 }
 ctx.globalAlpha=1;
 const tileSize=530,wx=Math.floor((cx-W*.5)/tileSize)-1,wy=Math.floor((cy-H*.5)/tileSize)-1;
 for(let y=wy;y<wy+4;y++)for(let x=wx;x<wx+4;x++){const h=hash(x,y,59);if(h<.53)continue;const sx=x*tileSize-cx+W*.5+tileSize*hash(x,y,11),sy=y*tileSize-cy+H*.51+tileSize*hash(x,y,15);if(sx<-130||sx>W+130||sy<-130||sy>H+130)continue;const r=26+hash(x,y,27)*46;
 ctx.save();ctx.translate(sx,sy);ctx.rotate(hash(x,y,34)*TAU);ctx.strokeStyle=h>.8?'#ad7edc38':'#73f9c331';ctx.lineWidth=1.4;ring(0,0,r,ctx.strokeStyle,1.2);ring(0,0,r*.76,ctx.strokeStyle,.6);for(let a=0;a<6;a++){const angle=a*TAU/6;line(Math.cos(angle)*r*.72,Math.sin(angle)*r*.72,Math.cos(angle)*r*1.15,Math.sin(angle)*r*1.15,ctx.strokeStyle,.7)}ctx.restore()}
 // Thousands of procedurally possible ruin cells; only visible tiles rendered.
 // Each location is absolute-world indexed, so its edges never jump on wrap.
 const cell=270,firstX=Math.floor((cx-W*.5)/cell)-1,firstY=Math.floor((cy-H*.51)/cell)-1;
 for(let yy=firstY;yy<firstY+Math.ceil(H/cell)+3;yy++)for(let xx=firstX;xx<firstX+Math.ceil(W/cell)+3;xx++){
   const seed=hash(xx,yy,83);if(seed<.69)continue;
   let x=xx*cell-cx+W*.5+hash(xx,yy,71)*cell,y=yy*cell-cy+H*.51+hash(xx,yy,72)*cell;
   if(x<-65||x>W+65||y<-65||y>H+65)continue;
   let radius=13+hash(xx,yy,76)*24,ang=hash(xx,yy,64)*TAU;
   ctx.save();ctx.translate(x,y);ctx.rotate(ang);ctx.globalAlpha=seed>.90?.38:.22;
   ctx.fillStyle='#1e2c47';ctx.strokeStyle=seed>.84?'#e7a66d':'#70c0b2';ctx.lineWidth=1;
   polygon(0,0,radius,seed>.8?6:5,.25);ctx.fill();ctx.stroke();
   ctx.globalAlpha=.18;polygon(0,0,radius*.62,5,Math.PI/4);ctx.stroke();
   line(-radius*.5,0,radius*.32,-radius*.22,seed>.84?'#fac692':'#9af7d0',1);
   ctx.restore();
 }
 const horizon=ctx.createRadialGradient(W*.5,H*.58,10,W*.5,H*.58,Math.max(W,H)*.77);horizon.addColorStop(0,'#19365917');horizon.addColorStop(1,'#03071000');ctx.fillStyle=horizon;ctx.fillRect(0,0,W,H)}
function drawHero(x,y,scale=1,rotation=0){const a=rotation;ctx.save();ctx.translate(x,y);ctx.rotate(a+Math.PI/2);ctx.scale(scale,scale);
 const fire=Math.sin(ambient*32)*3;ctx.globalAlpha=.8;let trail=ctx.createLinearGradient(0,12,0,30+fire);trail.addColorStop(0,'#84ffe9');trail.addColorStop(1,'#28ffd300');ctx.fillStyle=trail;ctx.beginPath();ctx.moveTo(-8,10);ctx.lineTo(0,27+fire);ctx.lineTo(8,10);ctx.closePath();ctx.fill();ctx.globalAlpha=1;
 ctx.shadowColor=COL.teal;ctx.shadowBlur=options.effects?18:5;ctx.strokeStyle='#c9ffee';ctx.lineWidth=2.2;ctx.fillStyle='#15293b';ctx.beginPath();ctx.moveTo(0,-20);ctx.lineTo(14,11);ctx.lineTo(8,15);ctx.lineTo(0,9);ctx.lineTo(-8,15);ctx.lineTo(-14,11);ctx.closePath();ctx.fill();ctx.stroke();ctx.shadowBlur=0;
 ctx.fillStyle='#60ead6';ctx.beginPath();ctx.moveTo(0,-15);ctx.lineTo(6,1);ctx.lineTo(0,10);ctx.lineTo(-6,1);ctx.closePath();ctx.fill();ctx.fillStyle='#ffb773';ctx.fillRect(-2,2,4,9);ctx.strokeStyle='#b5fff5';ctx.lineWidth=1.2;line(-11,12,-4,8,COL.teal,1);line(11,12,4,8,COL.teal,1);ctx.restore()}
function drawEnemy(e){let p=screenPos(e.x,e.y);if(p.x<-90||p.x>W+90||p.y<-90||p.y>H+90)return;ctx.save();ctx.translate(p.x,p.y);ctx.rotate(e.anim*.22);let color=e.type==='boss'?'#f7ac84':e.type==='bulwark'?'#c48cb1':e.type==='prism'?'#b99dff':'#f28999';ctx.shadowColor=color;ctx.shadowBlur=options.effects?8:0;ctx.fillStyle=e.hitFlash>0?'#ffffff':e.type==='prism'?'#3e295c':e.type==='boss'?'#372033':'#341b34';ctx.lineWidth=e.type==='boss'?3:2;ctx.strokeStyle=color;
 if(e.type==='wisp'){polygon(0,0,e.r,4,Math.PI/4);ctx.fill();ctx.stroke();ctx.fillStyle=color;polygon(0,0,e.r*.35,4,Math.PI/4);ctx.fill()}
 else if(e.type==='skitter'){polygon(0,0,e.r,3,-Math.PI/2);ctx.fill();ctx.stroke();ring(0,0,3,COL.mint,1)}
 else if(e.type==='prism'){polygon(0,0,e.r,6,Math.PI/6);ctx.fill();ctx.stroke();ctx.beginPath();ctx.moveTo(0,-13);ctx.lineTo(8,0);ctx.lineTo(0,13);ctx.lineTo(-8,0);ctx.closePath();ctx.fillStyle='#af8dfe';ctx.fill()}
 else if(e.type==='bulwark'){polygon(0,0,e.r,8,Math.PI/8);ctx.fill();ctx.stroke();ring(0,0,11,color,1);ctx.fillStyle='#ffced7';ctx.fillRect(-5,-5,10,10)}
 else if(e.type==='boss'){const spin=e.anim*.3;ctx.rotate(spin);for(let k=0;k<12;k++){let a=TAU*k/12;line(Math.cos(a)*e.r*.65,Math.sin(a)*e.r*.65,Math.cos(a)*e.r*1.43,Math.sin(a)*e.r*1.43,COL.coral,3)}polygon(0,0,e.r,8,Math.PI/8);ctx.fill();ctx.stroke();ring(0,0,e.r*.63,COL.gold,3);ctx.fillStyle='#ffc2a2';polygon(0,0,e.r*.34,6,Math.PI/6);ctx.fill();ring(0,0,e.r*1.32,'#ffb77e3f',1)}
 ctx.restore();
 if((e.type==='boss'||e.type==='prism')&&e.cd<.52&&e.cd>=0){
  const charge=1-e.cd/.52;
  ctx.save();ctx.globalAlpha=.25+.45*charge;
  ring(p.x,p.y,e.r+9+charge*23,e.type==='boss'?'#ff9378':'#bc9bff',1.5+charge*1.2);
  if(e.type==='boss'){for(let k=0;k<8;k++){
   const angle=k*TAU/8+e.anim*.3;
   line(p.x+Math.cos(angle)*(e.r+3),p.y+Math.sin(angle)*(e.r+3),
    p.x+Math.cos(angle)*(e.r+32),p.y+Math.sin(angle)*(e.r+32),'#ff9a76a0',1.2)
  }}ctx.restore()
 }
 if(e.hp<e.maxHp&&e.type!=='wisp'&&e.type!=='skitter'){ctx.fillStyle='#1f263b';ctx.fillRect(p.x-e.r,p.y-e.r-13,e.r*2,3);ctx.fillStyle=color;ctx.fillRect(p.x-e.r,p.y-e.r-13,e.r*2*e.hp/e.maxHp,3)}}
function drawShots(){for(const b of shots){const p=screenPos(b.x,b.y);if(p.x<-30||p.x>W+30||p.y<-30||p.y>H+30)continue;ctx.save();ctx.shadowColor=b.crit?COL.gold:COL.teal;ctx.shadowBlur=options.effects?13:0;ctx.strokeStyle=b.crit?COL.gold:COL.teal;ctx.lineWidth=b.crit?3.8:2.6;ctx.lineCap='round';ctx.beginPath();ctx.moveTo(p.x-b.vx*.024,p.y-b.vy*.024);ctx.lineTo(p.x,p.y);ctx.stroke();ctx.restore()}
 for(const b of hostileShots){const p=screenPos(b.x,b.y);ctx.save();ctx.shadowColor=b.color;ctx.shadowBlur=options.effects?9:0;ctx.fillStyle=b.color;ctx.beginPath();ctx.arc(p.x,p.y,b.r,0,TAU);ctx.fill();ctx.restore()}}
function drawPickups(){for(const p of pickups){const q=screenPos(p.x,p.y);if(q.x<-15||q.x>W+15||q.y<-15||q.y>H+15)continue;ctx.save();ctx.translate(q.x,q.y);ctx.rotate(ambient*2);ctx.fillStyle='#e8bf85';ctx.shadowColor=COL.gold;ctx.shadowBlur=options.effects?10:2;polygon(0,0,p.r,4,Math.PI/4);ctx.fill();ctx.restore()}}
function drawOrbitals(){if(!hero.orbit)return;for(let i=0;i<hero.orbit;i++){const a=orbAngle+i*TAU/hero.orbit,x=W*.5+Math.cos(a)*77,y=H*.51+Math.sin(a)*77;ctx.save();ctx.translate(x,y);ctx.rotate(a);ctx.shadowColor=COL.gold;ctx.shadowBlur=options.effects?20:0;ctx.fillStyle='#f7cb97';polygon(0,0,10,4,Math.PI/4);ctx.fill();ctx.restore()}}
function effects(){if(options.effects){ctx.save();for(const p of particles){const v=clamp(p.life/p.max,0,1);ctx.globalAlpha=v;ctx.fillStyle=p.color;ctx.fillRect(screenPos(p.x,p.y).x,screenPos(p.x,p.y).y,p.size,p.size)}ctx.restore()}
 for(const s of sparks){let p=screenPos(s.x,s.y),radius=lerp(5,s.max,1-s.life/s.maxLife);ctx.save();ctx.globalAlpha=clamp(s.life/s.maxLife,0,1);ctx.shadowColor=s.color;ctx.shadowBlur=options.effects?25:4;ring(p.x,p.y,radius,s.color,Math.max(1,s.life/s.maxLife*5));ctx.restore()}
 for(const f of floaters){let p=screenPos(f.x,f.y);ctx.save();ctx.globalAlpha=clamp(f.life/f.max,0,1);ctx.fillStyle=f.color;ctx.shadowColor=f.color;ctx.shadowBlur=options.effects?6:0;ctx.font='bold 13px system-ui';ctx.textAlign='center';ctx.fillText(f.label,p.x,p.y);ctx.restore()}}
function render(){ctx.setTransform(DPR,0,0,DPR,0,0);ctx.clearRect(0,0,W,H);ctx.save();if(shake>.1&&options.effects&&mode==='playing')ctx.translate(rand(-shake,shake),rand(-shake,shake));background();if(mode==='menu'||mode==='settings'&&previousMode==='menu'){let x=W*.49+Math.sin(ambient*.46)*10,y=H*.36+Math.sin(ambient*1.3)*7;ctx.save();ctx.globalAlpha=.35;const r=Math.min(W,H)*.37;ring(x,y,r,'#77fce750',1);ring(x,y,r*.79,'#f7ba7960',1);ctx.restore();drawHero(x,y,2.2,Math.sin(ambient*.6)*.25)}else{drawPickups();drawShots();for(const e of enemies)drawEnemy(e);drawOrbitals();if(options.effects){for(const g of afterimages){let p=screenPos(g.x,g.y);ctx.save();ctx.globalAlpha=clamp(g.life/.28,0,1)*.23;drawHero(p.x,p.y,.88,g.a);ctx.restore()}}
 if(hero.invuln<=0||Math.sin(ambient*40)>.0){ctx.save();ctx.shadowColor=COL.teal;ctx.shadowBlur=options.effects?20:5;ring(W*.5,H*.51,hero.r+5,'#7dfff142',1);ctx.restore();drawHero(W*.5,H*.51,1,hero.angle)}effects();if(flash>0){ctx.fillStyle='#fbb7a1';ctx.globalAlpha=flash*.24;ctx.fillRect(0,0,W,H);ctx.globalAlpha=1}}ctx.restore()}
function loop(timestamp){let dt=last?clamp((timestamp-last)/1000,0,.034):.016;last=timestamp;frames++;fpsTime+=dt;if(fpsTime>.9){measuredFps=Math.round(frames/fpsTime);UI.fps.textContent=measuredFps+' FPS';frames=0;fpsTime=0;if(options.quality==='AUTO'&&mode==='playing'){if(measuredFps<42&&fxScale>0.78){fxScale=.78;resize()}else if(measuredFps>57&&fxScale<1){fxScale=1;resize()}}}simulation(dt);if(frame%5===0&&mode==='playing')updateHud();render();requestAnimationFrame(loop)}
function direction(clientX,clientY,rect){let cx=rect.left+rect.width*.5,cy=rect.top+rect.height*.5,x=clientX-cx,y=clientY-cy,r=Math.min(50,rect.width*.37),len=Math.max(1,Math.hypot(x,y)),v=Math.min(len/r,1),xx=x/len*v,yy=y/len*v;motion.x=xx;motion.y=yy;UI.joyStick.style.transform=`translate(calc(-50% + ${xx*40}px),calc(-50% + ${yy*40}px))`}
UI.joyArea.addEventListener('pointerdown',e=>{if(mode!=='playing')return;e.preventDefault();pointerId=e.pointerId;UI.joyArea.setPointerCapture(pointerId);direction(e.clientX,e.clientY,UI.joyArea.getBoundingClientRect())});
UI.joyArea.addEventListener('pointermove',e=>{if(pointerId===e.pointerId)direction(e.clientX,e.clientY,UI.joyArea.getBoundingClientRect())});
function clearJoy(e){if(pointerId!==null&&(e.pointerId===pointerId||e.type==='blur')){pointerId=null;motion.x=motion.y=0;UI.joyStick.style.transform='translate(-50%,-50%)'}};
for(const t of ['pointerup','pointercancel','lostpointercapture'])UI.joyArea.addEventListener(t,clearJoy);window.addEventListener('blur',()=>{clearJoy({type:'blur'});if(mode==='playing')pauseGame()});
const keyMap={ArrowUp:'up',ArrowDown:'down',ArrowLeft:'left',ArrowRight:'right',w:'w',a:'a',s:'s',d:'d'};
window.addEventListener('keydown',e=>{let k=keyMap[e.key];if(k){keyDirections[k]=true;e.preventDefault()}if(e.key==='Escape'||e.key==='Backspace'){e.preventDefault();onBack()}if((e.key===' '||e.key.toLowerCase()==='e')&&mode==='playing'){e.preventDefault();activateNova()}});window.addEventListener('keyup',e=>{const k=keyMap[e.key];if(k)keyDirections[k]=false});
$('playBtn').addEventListener('click',resetRun);$('pauseBtn').addEventListener('click',pauseGame);$('resumeBtn').addEventListener('click',resume);$('pauseSettings').addEventListener('click',openSettings);$('quitBtn').addEventListener('click',openMenu);$('retryBtn').addEventListener('click',resetRun);$('endHomeBtn').addEventListener('click',openMenu);$('menuSettings').addEventListener('click',openSettings);$('closeSettings').addEventListener('click',closeSettings);UI.novaBtn.addEventListener('click',activateNova);
for(const name of ['Sound','Effects','Haptics','Fps'])$('toggle'+name).addEventListener('click',()=>{options[name.toLowerCase()]=!options[name.toLowerCase()];storeOptions();tone(660,.07,'triangle')});
$('toggleQuality').addEventListener('click',()=>{const choices=['AUTO','ECO','HIGH'];options.quality=choices[(choices.indexOf(options.quality)+1)%choices.length];storeOptions()});
function onBack(){if(mode==='settings'){closeSettings();return true}if(mode==='playing'){pauseGame();return true}if(mode==='paused'){resume();return true}if(mode==='upgrade'){return true}if(mode==='gameover'){openMenu();return true}return false}
window.addEventListener('resize',resize);
document.addEventListener('visibilitychange',()=>{if(document.hidden&&mode==='playing')pauseGame()});
window.Riftward=Object.freeze({status:()=>({state:mode,wave,kills,shards,elapsed:Math.round(elapsed*10)/10,hp:Math.max(0,Math.round(hero.hp)),position:[Math.round(hero.x),Math.round(hero.y)],boss:boss&&boss.hp>0?'alive':null,enemies:enemies.length,shots:shots.length,upgrades:hero.level-1,settings:{...options},fps:measuredFps,screen:[Math.round(W),Math.round(H)],version:'1.2.0'}),back:onBack,suspend:()=>{if(mode==='playing')pauseGame();return true}});
storeOptions();resize();openMenu();requestAnimationFrame(loop);
})();
