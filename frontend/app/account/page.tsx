'use client';
import {useState} from 'react';
export default function Account(){
 const [mode,setMode]=useState('login'),[message,setMessage]=useState('');
 const [profile,setProfile]=useState<Record<string,string>|null>(null);
 async function submit(e:React.FormEvent<HTMLFormElement>){
 e.preventDefault();setMessage('');
 const body=Object.fromEntries(new FormData(e.currentTarget));
 try{
 const res=await fetch('/api/auth/'+(mode==='profile'?'me':mode),{method:mode==='profile'?'PATCH':'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});
 const data=await res.json(); if(!res.ok){setMessage(typeof data.detail==='string'?data.detail:'Please check your input');return;}
 if(mode==='login'||mode==='profile')setProfile(data);
 if(mode==='logout')setProfile(null);
 setMessage(data.message||'Saved');
 }catch{setMessage('Service unavailable');}
 }
 return <main style={{minHeight:'100vh',display:'grid',placeItems:'center',background:'#0b1220',color:'#e2e8f0',fontFamily:'system-ui'}}><section style={{width:'min(90vw,420px)',padding:32,background:'#172235',borderRadius:16,boxSizing:'border-box'}}><h1>GRTAlgo</h1><p>Secure account access · Paper trading only</p>{profile&&<p>Signed in as {profile.name}</p>}<h2>{mode}</h2><form key={mode} onSubmit={submit} style={{display:'grid',gap:12}}>{['login','register','forgot','resend'].includes(mode)&&<label>Email<input style={{display:'block',width:'100%'}} name="email" type="email" required/></label>}{['register','profile'].includes(mode)&&<label>Name<input name="name" required maxLength={100}/></label>}{['verify','reset'].includes(mode)&&<label>One-time code<input name="token" required/></label>}{['login','register','reset'].includes(mode)&&<label>Password<input name="password" type="password" minLength={12} maxLength={128} required/></label>}<button style={{padding:12,background:'#2563eb',color:'white',border:0,borderRadius:8}}>Continue</button></form><p role="status">{message}</p><nav style={{display:'flex',flexWrap:'wrap',gap:8}}>{['login','register','verify','resend','forgot','reset','profile','logout'].map(m=><button key={m} onClick={()=>{setMode(m);setMessage('')}}>{m}</button>)}</nav></section></main>
}
