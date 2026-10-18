(()=>{var fd=0,Al=1,pd=2;var Cl=1,md=2,In=3,Vn=0,zt=1,dn=2,Xn=0,wi=1,Rl=2,Il=3,Pl=4,gd=5,ri=100,xd=101,_d=102,yd=103,vd=104,bd=200,wd=201,Md=202,Sd=203,aa=204,oa=205,Ed=206,Td=207,Ad=208,Cd=209,Rd=210,Id=211,Pd=212,Nd=213,Dd=214,Da=0,La=1,Fa=2,Mi=3,Ua=4,Oa=5,Ba=6,za=7,Nl=0,Ld=1,Fd=2,$n=0,Ud=1,Od=2,Bd=3,zd=4,kd=5,Hd=6,Vd=7;var Dl=300,Ai=301,Ci=302,ka=303,Ha=304,hs=306,la=1e3,ii=1001,ca=1002,cn=1003,Gd=1004;var fs=1005;var vn=1006,Va=1007;var ui=1008;var Mn=1009,Ll=1010,Fl=1011,gr=1012,Ga=1013,hi=1014,Pn=1015,xr=1016,Wa=1017,Xa=1018,_r=1020,Ul=35902,Ol=35899,Bl=1021,zl=1022,un=1023,or=1026,yr=1027,kl=1028,$a=1029,Hl=1030,qa=1031;var Ya=1033,ps=33776,ms=33777,gs=33778,xs=33779,Za=35840,Ja=35841,Ka=35842,ja=35843,Qa=36196,eo=37492,to=37496,no=37808,io=37809,ro=37810,so=37811,ao=37812,oo=37813,lo=37814,co=37815,uo=37816,ho=37817,fo=37818,po=37819,mo=37820,go=37821,xo=36492,_o=36494,yo=36495,vo=36283,bo=36284,wo=36285,Mo=36286;var zr=2300,da=2301,sa=2302,yl=2400,vl=2401,bl=2402;var Wd=3200,Xd=3201;var Vl=0,$d=1,qn="",Nt="srgb",Si="srgb-linear",kr="linear",Ke="srgb";var bi=7680;var wl=519,qd=512,Yd=513,Zd=514,Gl=515,Jd=516,Kd=517,jd=518,Qd=519,ua=35044;var Wl="300 es",yn=2e3,Hr=2001;var Gn=class{addEventListener(e,t){this._listeners===void 0&&(this._listeners={});let n=this._listeners;n[e]===void 0&&(n[e]=[]),n[e].indexOf(t)===-1&&n[e].push(t)}hasEventListener(e,t){let n=this._listeners;return n===void 0?!1:n[e]!==void 0&&n[e].indexOf(t)!==-1}removeEventListener(e,t){let n=this._listeners;if(n===void 0)return;let r=n[e];if(r!==void 0){let s=r.indexOf(t);s!==-1&&r.splice(s,1)}}dispatchEvent(e){let t=this._listeners;if(t===void 0)return;let n=t[e.type];if(n!==void 0){e.target=this;let r=n.slice(0);for(let s=0,a=r.length;s<a;s++)r[s].call(this,e);e.target=null}}},It=["00","01","02","03","04","05","06","07","08","09","0a","0b","0c","0d","0e","0f","10","11","12","13","14","15","16","17","18","19","1a","1b","1c","1d","1e","1f","20","21","22","23","24","25","26","27","28","29","2a","2b","2c","2d","2e","2f","30","31","32","33","34","35","36","37","38","39","3a","3b","3c","3d","3e","3f","40","41","42","43","44","45","46","47","48","49","4a","4b","4c","4d","4e","4f","50","51","52","53","54","55","56","57","58","59","5a","5b","5c","5d","5e","5f","60","61","62","63","64","65","66","67","68","69","6a","6b","6c","6d","6e","6f","70","71","72","73","74","75","76","77","78","79","7a","7b","7c","7d","7e","7f","80","81","82","83","84","85","86","87","88","89","8a","8b","8c","8d","8e","8f","90","91","92","93","94","95","96","97","98","99","9a","9b","9c","9d","9e","9f","a0","a1","a2","a3","a4","a5","a6","a7","a8","a9","aa","ab","ac","ad","ae","af","b0","b1","b2","b3","b4","b5","b6","b7","b8","b9","ba","bb","bc","bd","be","bf","c0","c1","c2","c3","c4","c5","c6","c7","c8","c9","ca","cb","cc","cd","ce","cf","d0","d1","d2","d3","d4","d5","d6","d7","d8","d9","da","db","dc","dd","de","df","e0","e1","e2","e3","e4","e5","e6","e7","e8","e9","ea","eb","ec","ed","ee","ef","f0","f1","f2","f3","f4","f5","f6","f7","f8","f9","fa","fb","fc","fd","fe","ff"],Bc=1234567,sr=Math.PI/180,lr=180/Math.PI;function kn(){let i=Math.random()*4294967295|0,e=Math.random()*4294967295|0,t=Math.random()*4294967295|0,n=Math.random()*4294967295|0;return(It[i&255]+It[i>>8&255]+It[i>>16&255]+It[i>>24&255]+"-"+It[e&255]+It[e>>8&255]+"-"+It[e>>16&15|64]+It[e>>24&255]+"-"+It[t&63|128]+It[t>>8&255]+"-"+It[t>>16&255]+It[t>>24&255]+It[n&255]+It[n>>8&255]+It[n>>16&255]+It[n>>24&255]).toLowerCase()}function Ge(i,e,t){return Math.max(e,Math.min(t,i))}function Xl(i,e){return(i%e+e)%e}function Th(i,e,t,n,r){return n+(i-e)*(r-n)/(t-e)}function Ah(i,e,t){return i!==e?(t-i)/(e-i):0}function Br(i,e,t){return(1-t)*i+t*e}function Ch(i,e,t,n){return Br(i,e,1-Math.exp(-t*n))}function Rh(i,e=1){return e-Math.abs(Xl(i,e*2)-e)}function Ih(i,e,t){return i<=e?0:i>=t?1:(i=(i-e)/(t-e),i*i*(3-2*i))}function Ph(i,e,t){return i<=e?0:i>=t?1:(i=(i-e)/(t-e),i*i*i*(i*(i*6-15)+10))}function Nh(i,e){return i+Math.floor(Math.random()*(e-i+1))}function Dh(i,e){return i+Math.random()*(e-i)}function Lh(i){return i*(.5-Math.random())}function Fh(i){i!==void 0&&(Bc=i);let e=Bc+=1831565813;return e=Math.imul(e^e>>>15,e|1),e^=e+Math.imul(e^e>>>7,e|61),((e^e>>>14)>>>0)/4294967296}function Uh(i){return i*sr}function Oh(i){return i*lr}function Bh(i){return(i&i-1)===0&&i!==0}function zh(i){return Math.pow(2,Math.ceil(Math.log(i)/Math.LN2))}function kh(i){return Math.pow(2,Math.floor(Math.log(i)/Math.LN2))}function Hh(i,e,t,n,r){let s=Math.cos,a=Math.sin,o=s(t/2),l=a(t/2),c=s((e+n)/2),d=a((e+n)/2),u=s((e-n)/2),h=a((e-n)/2),p=s((n-e)/2),g=a((n-e)/2);switch(r){case"XYX":i.set(o*d,l*u,l*h,o*c);break;case"YZY":i.set(l*h,o*d,l*u,o*c);break;case"ZXZ":i.set(l*u,l*h,o*d,o*c);break;case"XZX":i.set(o*d,l*g,l*p,o*c);break;case"YXY":i.set(l*p,o*d,l*g,o*c);break;case"ZYZ":i.set(l*g,l*p,o*d,o*c);break;default:console.warn("THREE.MathUtils: .setQuaternionFromProperEuler() encountered an unknown order: "+r)}}function _n(i,e){switch(e.constructor){case Float32Array:return i;case Uint32Array:return i/4294967295;case Uint16Array:return i/65535;case Uint8Array:return i/255;case Int32Array:return Math.max(i/2147483647,-1);case Int16Array:return Math.max(i/32767,-1);case Int8Array:return Math.max(i/127,-1);default:throw new Error("Invalid component type.")}}function Je(i,e){switch(e.constructor){case Float32Array:return i;case Uint32Array:return Math.round(i*4294967295);case Uint16Array:return Math.round(i*65535);case Uint8Array:return Math.round(i*255);case Int32Array:return Math.round(i*2147483647);case Int16Array:return Math.round(i*32767);case Int8Array:return Math.round(i*127);default:throw new Error("Invalid component type.")}}var yt={DEG2RAD:sr,RAD2DEG:lr,generateUUID:kn,clamp:Ge,euclideanModulo:Xl,mapLinear:Th,inverseLerp:Ah,lerp:Br,damp:Ch,pingpong:Rh,smoothstep:Ih,smootherstep:Ph,randInt:Nh,randFloat:Dh,randFloatSpread:Lh,seededRandom:Fh,degToRad:Uh,radToDeg:Oh,isPowerOfTwo:Bh,ceilPowerOfTwo:zh,floorPowerOfTwo:kh,setQuaternionFromProperEuler:Hh,normalize:Je,denormalize:_n},He=class i{constructor(e=0,t=0){i.prototype.isVector2=!0,this.x=e,this.y=t}get width(){return this.x}set width(e){this.x=e}get height(){return this.y}set height(e){this.y=e}set(e,t){return this.x=e,this.y=t,this}setScalar(e){return this.x=e,this.y=e,this}setX(e){return this.x=e,this}setY(e){return this.y=e,this}setComponent(e,t){switch(e){case 0:this.x=t;break;case 1:this.y=t;break;default:throw new Error("index is out of range: "+e)}return this}getComponent(e){switch(e){case 0:return this.x;case 1:return this.y;default:throw new Error("index is out of range: "+e)}}clone(){return new this.constructor(this.x,this.y)}copy(e){return this.x=e.x,this.y=e.y,this}add(e){return this.x+=e.x,this.y+=e.y,this}addScalar(e){return this.x+=e,this.y+=e,this}addVectors(e,t){return this.x=e.x+t.x,this.y=e.y+t.y,this}addScaledVector(e,t){return this.x+=e.x*t,this.y+=e.y*t,this}sub(e){return this.x-=e.x,this.y-=e.y,this}subScalar(e){return this.x-=e,this.y-=e,this}subVectors(e,t){return this.x=e.x-t.x,this.y=e.y-t.y,this}multiply(e){return this.x*=e.x,this.y*=e.y,this}multiplyScalar(e){return this.x*=e,this.y*=e,this}divide(e){return this.x/=e.x,this.y/=e.y,this}divideScalar(e){return this.multiplyScalar(1/e)}applyMatrix3(e){let t=this.x,n=this.y,r=e.elements;return this.x=r[0]*t+r[3]*n+r[6],this.y=r[1]*t+r[4]*n+r[7],this}min(e){return this.x=Math.min(this.x,e.x),this.y=Math.min(this.y,e.y),this}max(e){return this.x=Math.max(this.x,e.x),this.y=Math.max(this.y,e.y),this}clamp(e,t){return this.x=Ge(this.x,e.x,t.x),this.y=Ge(this.y,e.y,t.y),this}clampScalar(e,t){return this.x=Ge(this.x,e,t),this.y=Ge(this.y,e,t),this}clampLength(e,t){let n=this.length();return this.divideScalar(n||1).multiplyScalar(Ge(n,e,t))}floor(){return this.x=Math.floor(this.x),this.y=Math.floor(this.y),this}ceil(){return this.x=Math.ceil(this.x),this.y=Math.ceil(this.y),this}round(){return this.x=Math.round(this.x),this.y=Math.round(this.y),this}roundToZero(){return this.x=Math.trunc(this.x),this.y=Math.trunc(this.y),this}negate(){return this.x=-this.x,this.y=-this.y,this}dot(e){return this.x*e.x+this.y*e.y}cross(e){return this.x*e.y-this.y*e.x}lengthSq(){return this.x*this.x+this.y*this.y}length(){return Math.sqrt(this.x*this.x+this.y*this.y)}manhattanLength(){return Math.abs(this.x)+Math.abs(this.y)}normalize(){return this.divideScalar(this.length()||1)}angle(){return Math.atan2(-this.y,-this.x)+Math.PI}angleTo(e){let t=Math.sqrt(this.lengthSq()*e.lengthSq());if(t===0)return Math.PI/2;let n=this.dot(e)/t;return Math.acos(Ge(n,-1,1))}distanceTo(e){return Math.sqrt(this.distanceToSquared(e))}distanceToSquared(e){let t=this.x-e.x,n=this.y-e.y;return t*t+n*n}manhattanDistanceTo(e){return Math.abs(this.x-e.x)+Math.abs(this.y-e.y)}setLength(e){return this.normalize().multiplyScalar(e)}lerp(e,t){return this.x+=(e.x-this.x)*t,this.y+=(e.y-this.y)*t,this}lerpVectors(e,t,n){return this.x=e.x+(t.x-e.x)*n,this.y=e.y+(t.y-e.y)*n,this}equals(e){return e.x===this.x&&e.y===this.y}fromArray(e,t=0){return this.x=e[t],this.y=e[t+1],this}toArray(e=[],t=0){return e[t]=this.x,e[t+1]=this.y,e}fromBufferAttribute(e,t){return this.x=e.getX(t),this.y=e.getY(t),this}rotateAround(e,t){let n=Math.cos(t),r=Math.sin(t),s=this.x-e.x,a=this.y-e.y;return this.x=s*n-a*r+e.x,this.y=s*r+a*n+e.y,this}random(){return this.x=Math.random(),this.y=Math.random(),this}*[Symbol.iterator](){yield this.x,yield this.y}},Wt=class{constructor(e=0,t=0,n=0,r=1){this.isQuaternion=!0,this._x=e,this._y=t,this._z=n,this._w=r}static slerpFlat(e,t,n,r,s,a,o){let l=n[r+0],c=n[r+1],d=n[r+2],u=n[r+3],h=s[a+0],p=s[a+1],g=s[a+2],x=s[a+3];if(o===0){e[t+0]=l,e[t+1]=c,e[t+2]=d,e[t+3]=u;return}if(o===1){e[t+0]=h,e[t+1]=p,e[t+2]=g,e[t+3]=x;return}if(u!==x||l!==h||c!==p||d!==g){let m=1-o,f=l*h+c*p+d*g+u*x,S=f>=0?1:-1,M=1-f*f;if(M>Number.EPSILON){let C=Math.sqrt(M),E=Math.atan2(C,f*S);m=Math.sin(m*E)/C,o=Math.sin(o*E)/C}let y=o*S;if(l=l*m+h*y,c=c*m+p*y,d=d*m+g*y,u=u*m+x*y,m===1-o){let C=1/Math.sqrt(l*l+c*c+d*d+u*u);l*=C,c*=C,d*=C,u*=C}}e[t]=l,e[t+1]=c,e[t+2]=d,e[t+3]=u}static multiplyQuaternionsFlat(e,t,n,r,s,a){let o=n[r],l=n[r+1],c=n[r+2],d=n[r+3],u=s[a],h=s[a+1],p=s[a+2],g=s[a+3];return e[t]=o*g+d*u+l*p-c*h,e[t+1]=l*g+d*h+c*u-o*p,e[t+2]=c*g+d*p+o*h-l*u,e[t+3]=d*g-o*u-l*h-c*p,e}get x(){return this._x}set x(e){this._x=e,this._onChangeCallback()}get y(){return this._y}set y(e){this._y=e,this._onChangeCallback()}get z(){return this._z}set z(e){this._z=e,this._onChangeCallback()}get w(){return this._w}set w(e){this._w=e,this._onChangeCallback()}set(e,t,n,r){return this._x=e,this._y=t,this._z=n,this._w=r,this._onChangeCallback(),this}clone(){return new this.constructor(this._x,this._y,this._z,this._w)}copy(e){return this._x=e.x,this._y=e.y,this._z=e.z,this._w=e.w,this._onChangeCallback(),this}setFromEuler(e,t=!0){let n=e._x,r=e._y,s=e._z,a=e._order,o=Math.cos,l=Math.sin,c=o(n/2),d=o(r/2),u=o(s/2),h=l(n/2),p=l(r/2),g=l(s/2);switch(a){case"XYZ":this._x=h*d*u+c*p*g,this._y=c*p*u-h*d*g,this._z=c*d*g+h*p*u,this._w=c*d*u-h*p*g;break;case"YXZ":this._x=h*d*u+c*p*g,this._y=c*p*u-h*d*g,this._z=c*d*g-h*p*u,this._w=c*d*u+h*p*g;break;case"ZXY":this._x=h*d*u-c*p*g,this._y=c*p*u+h*d*g,this._z=c*d*g+h*p*u,this._w=c*d*u-h*p*g;break;case"ZYX":this._x=h*d*u-c*p*g,this._y=c*p*u+h*d*g,this._z=c*d*g-h*p*u,this._w=c*d*u+h*p*g;break;case"YZX":this._x=h*d*u+c*p*g,this._y=c*p*u+h*d*g,this._z=c*d*g-h*p*u,this._w=c*d*u-h*p*g;break;case"XZY":this._x=h*d*u-c*p*g,this._y=c*p*u-h*d*g,this._z=c*d*g+h*p*u,this._w=c*d*u+h*p*g;break;default:console.warn("THREE.Quaternion: .setFromEuler() encountered an unknown order: "+a)}return t===!0&&this._onChangeCallback(),this}setFromAxisAngle(e,t){let n=t/2,r=Math.sin(n);return this._x=e.x*r,this._y=e.y*r,this._z=e.z*r,this._w=Math.cos(n),this._onChangeCallback(),this}setFromRotationMatrix(e){let t=e.elements,n=t[0],r=t[4],s=t[8],a=t[1],o=t[5],l=t[9],c=t[2],d=t[6],u=t[10],h=n+o+u;if(h>0){let p=.5/Math.sqrt(h+1);this._w=.25/p,this._x=(d-l)*p,this._y=(s-c)*p,this._z=(a-r)*p}else if(n>o&&n>u){let p=2*Math.sqrt(1+n-o-u);this._w=(d-l)/p,this._x=.25*p,this._y=(r+a)/p,this._z=(s+c)/p}else if(o>u){let p=2*Math.sqrt(1+o-n-u);this._w=(s-c)/p,this._x=(r+a)/p,this._y=.25*p,this._z=(l+d)/p}else{let p=2*Math.sqrt(1+u-n-o);this._w=(a-r)/p,this._x=(s+c)/p,this._y=(l+d)/p,this._z=.25*p}return this._onChangeCallback(),this}setFromUnitVectors(e,t){let n=e.dot(t)+1;return n<1e-8?(n=0,Math.abs(e.x)>Math.abs(e.z)?(this._x=-e.y,this._y=e.x,this._z=0,this._w=n):(this._x=0,this._y=-e.z,this._z=e.y,this._w=n)):(this._x=e.y*t.z-e.z*t.y,this._y=e.z*t.x-e.x*t.z,this._z=e.x*t.y-e.y*t.x,this._w=n),this.normalize()}angleTo(e){return 2*Math.acos(Math.abs(Ge(this.dot(e),-1,1)))}rotateTowards(e,t){let n=this.angleTo(e);if(n===0)return this;let r=Math.min(1,t/n);return this.slerp(e,r),this}identity(){return this.set(0,0,0,1)}invert(){return this.conjugate()}conjugate(){return this._x*=-1,this._y*=-1,this._z*=-1,this._onChangeCallback(),this}dot(e){return this._x*e._x+this._y*e._y+this._z*e._z+this._w*e._w}lengthSq(){return this._x*this._x+this._y*this._y+this._z*this._z+this._w*this._w}length(){return Math.sqrt(this._x*this._x+this._y*this._y+this._z*this._z+this._w*this._w)}normalize(){let e=this.length();return e===0?(this._x=0,this._y=0,this._z=0,this._w=1):(e=1/e,this._x=this._x*e,this._y=this._y*e,this._z=this._z*e,this._w=this._w*e),this._onChangeCallback(),this}multiply(e){return this.multiplyQuaternions(this,e)}premultiply(e){return this.multiplyQuaternions(e,this)}multiplyQuaternions(e,t){let n=e._x,r=e._y,s=e._z,a=e._w,o=t._x,l=t._y,c=t._z,d=t._w;return this._x=n*d+a*o+r*c-s*l,this._y=r*d+a*l+s*o-n*c,this._z=s*d+a*c+n*l-r*o,this._w=a*d-n*o-r*l-s*c,this._onChangeCallback(),this}slerp(e,t){if(t===0)return this;if(t===1)return this.copy(e);let n=this._x,r=this._y,s=this._z,a=this._w,o=a*e._w+n*e._x+r*e._y+s*e._z;if(o<0?(this._w=-e._w,this._x=-e._x,this._y=-e._y,this._z=-e._z,o=-o):this.copy(e),o>=1)return this._w=a,this._x=n,this._y=r,this._z=s,this;let l=1-o*o;if(l<=Number.EPSILON){let p=1-t;return this._w=p*a+t*this._w,this._x=p*n+t*this._x,this._y=p*r+t*this._y,this._z=p*s+t*this._z,this.normalize(),this}let c=Math.sqrt(l),d=Math.atan2(c,o),u=Math.sin((1-t)*d)/c,h=Math.sin(t*d)/c;return this._w=a*u+this._w*h,this._x=n*u+this._x*h,this._y=r*u+this._y*h,this._z=s*u+this._z*h,this._onChangeCallback(),this}slerpQuaternions(e,t,n){return this.copy(e).slerp(t,n)}random(){let e=2*Math.PI*Math.random(),t=2*Math.PI*Math.random(),n=Math.random(),r=Math.sqrt(1-n),s=Math.sqrt(n);return this.set(r*Math.sin(e),r*Math.cos(e),s*Math.sin(t),s*Math.cos(t))}equals(e){return e._x===this._x&&e._y===this._y&&e._z===this._z&&e._w===this._w}fromArray(e,t=0){return this._x=e[t],this._y=e[t+1],this._z=e[t+2],this._w=e[t+3],this._onChangeCallback(),this}toArray(e=[],t=0){return e[t]=this._x,e[t+1]=this._y,e[t+2]=this._z,e[t+3]=this._w,e}fromBufferAttribute(e,t){return this._x=e.getX(t),this._y=e.getY(t),this._z=e.getZ(t),this._w=e.getW(t),this._onChangeCallback(),this}toJSON(){return this.toArray()}_onChange(e){return this._onChangeCallback=e,this}_onChangeCallback(){}*[Symbol.iterator](){yield this._x,yield this._y,yield this._z,yield this._w}},N=class i{constructor(e=0,t=0,n=0){i.prototype.isVector3=!0,this.x=e,this.y=t,this.z=n}set(e,t,n){return n===void 0&&(n=this.z),this.x=e,this.y=t,this.z=n,this}setScalar(e){return this.x=e,this.y=e,this.z=e,this}setX(e){return this.x=e,this}setY(e){return this.y=e,this}setZ(e){return this.z=e,this}setComponent(e,t){switch(e){case 0:this.x=t;break;case 1:this.y=t;break;case 2:this.z=t;break;default:throw new Error("index is out of range: "+e)}return this}getComponent(e){switch(e){case 0:return this.x;case 1:return this.y;case 2:return this.z;default:throw new Error("index is out of range: "+e)}}clone(){return new this.constructor(this.x,this.y,this.z)}copy(e){return this.x=e.x,this.y=e.y,this.z=e.z,this}add(e){return this.x+=e.x,this.y+=e.y,this.z+=e.z,this}addScalar(e){return this.x+=e,this.y+=e,this.z+=e,this}addVectors(e,t){return this.x=e.x+t.x,this.y=e.y+t.y,this.z=e.z+t.z,this}addScaledVector(e,t){return this.x+=e.x*t,this.y+=e.y*t,this.z+=e.z*t,this}sub(e){return this.x-=e.x,this.y-=e.y,this.z-=e.z,this}subScalar(e){return this.x-=e,this.y-=e,this.z-=e,this}subVectors(e,t){return this.x=e.x-t.x,this.y=e.y-t.y,this.z=e.z-t.z,this}multiply(e){return this.x*=e.x,this.y*=e.y,this.z*=e.z,this}multiplyScalar(e){return this.x*=e,this.y*=e,this.z*=e,this}multiplyVectors(e,t){return this.x=e.x*t.x,this.y=e.y*t.y,this.z=e.z*t.z,this}applyEuler(e){return this.applyQuaternion(zc.setFromEuler(e))}applyAxisAngle(e,t){return this.applyQuaternion(zc.setFromAxisAngle(e,t))}applyMatrix3(e){let t=this.x,n=this.y,r=this.z,s=e.elements;return this.x=s[0]*t+s[3]*n+s[6]*r,this.y=s[1]*t+s[4]*n+s[7]*r,this.z=s[2]*t+s[5]*n+s[8]*r,this}applyNormalMatrix(e){return this.applyMatrix3(e).normalize()}applyMatrix4(e){let t=this.x,n=this.y,r=this.z,s=e.elements,a=1/(s[3]*t+s[7]*n+s[11]*r+s[15]);return this.x=(s[0]*t+s[4]*n+s[8]*r+s[12])*a,this.y=(s[1]*t+s[5]*n+s[9]*r+s[13])*a,this.z=(s[2]*t+s[6]*n+s[10]*r+s[14])*a,this}applyQuaternion(e){let t=this.x,n=this.y,r=this.z,s=e.x,a=e.y,o=e.z,l=e.w,c=2*(a*r-o*n),d=2*(o*t-s*r),u=2*(s*n-a*t);return this.x=t+l*c+a*u-o*d,this.y=n+l*d+o*c-s*u,this.z=r+l*u+s*d-a*c,this}project(e){return this.applyMatrix4(e.matrixWorldInverse).applyMatrix4(e.projectionMatrix)}unproject(e){return this.applyMatrix4(e.projectionMatrixInverse).applyMatrix4(e.matrixWorld)}transformDirection(e){let t=this.x,n=this.y,r=this.z,s=e.elements;return this.x=s[0]*t+s[4]*n+s[8]*r,this.y=s[1]*t+s[5]*n+s[9]*r,this.z=s[2]*t+s[6]*n+s[10]*r,this.normalize()}divide(e){return this.x/=e.x,this.y/=e.y,this.z/=e.z,this}divideScalar(e){return this.multiplyScalar(1/e)}min(e){return this.x=Math.min(this.x,e.x),this.y=Math.min(this.y,e.y),this.z=Math.min(this.z,e.z),this}max(e){return this.x=Math.max(this.x,e.x),this.y=Math.max(this.y,e.y),this.z=Math.max(this.z,e.z),this}clamp(e,t){return this.x=Ge(this.x,e.x,t.x),this.y=Ge(this.y,e.y,t.y),this.z=Ge(this.z,e.z,t.z),this}clampScalar(e,t){return this.x=Ge(this.x,e,t),this.y=Ge(this.y,e,t),this.z=Ge(this.z,e,t),this}clampLength(e,t){let n=this.length();return this.divideScalar(n||1).multiplyScalar(Ge(n,e,t))}floor(){return this.x=Math.floor(this.x),this.y=Math.floor(this.y),this.z=Math.floor(this.z),this}ceil(){return this.x=Math.ceil(this.x),this.y=Math.ceil(this.y),this.z=Math.ceil(this.z),this}round(){return this.x=Math.round(this.x),this.y=Math.round(this.y),this.z=Math.round(this.z),this}roundToZero(){return this.x=Math.trunc(this.x),this.y=Math.trunc(this.y),this.z=Math.trunc(this.z),this}negate(){return this.x=-this.x,this.y=-this.y,this.z=-this.z,this}dot(e){return this.x*e.x+this.y*e.y+this.z*e.z}lengthSq(){return this.x*this.x+this.y*this.y+this.z*this.z}length(){return Math.sqrt(this.x*this.x+this.y*this.y+this.z*this.z)}manhattanLength(){return Math.abs(this.x)+Math.abs(this.y)+Math.abs(this.z)}normalize(){return this.divideScalar(this.length()||1)}setLength(e){return this.normalize().multiplyScalar(e)}lerp(e,t){return this.x+=(e.x-this.x)*t,this.y+=(e.y-this.y)*t,this.z+=(e.z-this.z)*t,this}lerpVectors(e,t,n){return this.x=e.x+(t.x-e.x)*n,this.y=e.y+(t.y-e.y)*n,this.z=e.z+(t.z-e.z)*n,this}cross(e){return this.crossVectors(this,e)}crossVectors(e,t){let n=e.x,r=e.y,s=e.z,a=t.x,o=t.y,l=t.z;return this.x=r*l-s*o,this.y=s*a-n*l,this.z=n*o-r*a,this}projectOnVector(e){let t=e.lengthSq();if(t===0)return this.set(0,0,0);let n=e.dot(this)/t;return this.copy(e).multiplyScalar(n)}projectOnPlane(e){return qo.copy(this).projectOnVector(e),this.sub(qo)}reflect(e){return this.sub(qo.copy(e).multiplyScalar(2*this.dot(e)))}angleTo(e){let t=Math.sqrt(this.lengthSq()*e.lengthSq());if(t===0)return Math.PI/2;let n=this.dot(e)/t;return Math.acos(Ge(n,-1,1))}distanceTo(e){return Math.sqrt(this.distanceToSquared(e))}distanceToSquared(e){let t=this.x-e.x,n=this.y-e.y,r=this.z-e.z;return t*t+n*n+r*r}manhattanDistanceTo(e){return Math.abs(this.x-e.x)+Math.abs(this.y-e.y)+Math.abs(this.z-e.z)}setFromSpherical(e){return this.setFromSphericalCoords(e.radius,e.phi,e.theta)}setFromSphericalCoords(e,t,n){let r=Math.sin(t)*e;return this.x=r*Math.sin(n),this.y=Math.cos(t)*e,this.z=r*Math.cos(n),this}setFromCylindrical(e){return this.setFromCylindricalCoords(e.radius,e.theta,e.y)}setFromCylindricalCoords(e,t,n){return this.x=e*Math.sin(t),this.y=n,this.z=e*Math.cos(t),this}setFromMatrixPosition(e){let t=e.elements;return this.x=t[12],this.y=t[13],this.z=t[14],this}setFromMatrixScale(e){let t=this.setFromMatrixColumn(e,0).length(),n=this.setFromMatrixColumn(e,1).length(),r=this.setFromMatrixColumn(e,2).length();return this.x=t,this.y=n,this.z=r,this}setFromMatrixColumn(e,t){return this.fromArray(e.elements,t*4)}setFromMatrix3Column(e,t){return this.fromArray(e.elements,t*3)}setFromEuler(e){return this.x=e._x,this.y=e._y,this.z=e._z,this}setFromColor(e){return this.x=e.r,this.y=e.g,this.z=e.b,this}equals(e){return e.x===this.x&&e.y===this.y&&e.z===this.z}fromArray(e,t=0){return this.x=e[t],this.y=e[t+1],this.z=e[t+2],this}toArray(e=[],t=0){return e[t]=this.x,e[t+1]=this.y,e[t+2]=this.z,e}fromBufferAttribute(e,t){return this.x=e.getX(t),this.y=e.getY(t),this.z=e.getZ(t),this}random(){return this.x=Math.random(),this.y=Math.random(),this.z=Math.random(),this}randomDirection(){let e=Math.random()*Math.PI*2,t=Math.random()*2-1,n=Math.sqrt(1-t*t);return this.x=n*Math.cos(e),this.y=t,this.z=n*Math.sin(e),this}*[Symbol.iterator](){yield this.x,yield this.y,yield this.z}},qo=new N,zc=new Wt,Oe=class i{constructor(e,t,n,r,s,a,o,l,c){i.prototype.isMatrix3=!0,this.elements=[1,0,0,0,1,0,0,0,1],e!==void 0&&this.set(e,t,n,r,s,a,o,l,c)}set(e,t,n,r,s,a,o,l,c){let d=this.elements;return d[0]=e,d[1]=r,d[2]=o,d[3]=t,d[4]=s,d[5]=l,d[6]=n,d[7]=a,d[8]=c,this}identity(){return this.set(1,0,0,0,1,0,0,0,1),this}copy(e){let t=this.elements,n=e.elements;return t[0]=n[0],t[1]=n[1],t[2]=n[2],t[3]=n[3],t[4]=n[4],t[5]=n[5],t[6]=n[6],t[7]=n[7],t[8]=n[8],this}extractBasis(e,t,n){return e.setFromMatrix3Column(this,0),t.setFromMatrix3Column(this,1),n.setFromMatrix3Column(this,2),this}setFromMatrix4(e){let t=e.elements;return this.set(t[0],t[4],t[8],t[1],t[5],t[9],t[2],t[6],t[10]),this}multiply(e){return this.multiplyMatrices(this,e)}premultiply(e){return this.multiplyMatrices(e,this)}multiplyMatrices(e,t){let n=e.elements,r=t.elements,s=this.elements,a=n[0],o=n[3],l=n[6],c=n[1],d=n[4],u=n[7],h=n[2],p=n[5],g=n[8],x=r[0],m=r[3],f=r[6],S=r[1],M=r[4],y=r[7],C=r[2],E=r[5],R=r[8];return s[0]=a*x+o*S+l*C,s[3]=a*m+o*M+l*E,s[6]=a*f+o*y+l*R,s[1]=c*x+d*S+u*C,s[4]=c*m+d*M+u*E,s[7]=c*f+d*y+u*R,s[2]=h*x+p*S+g*C,s[5]=h*m+p*M+g*E,s[8]=h*f+p*y+g*R,this}multiplyScalar(e){let t=this.elements;return t[0]*=e,t[3]*=e,t[6]*=e,t[1]*=e,t[4]*=e,t[7]*=e,t[2]*=e,t[5]*=e,t[8]*=e,this}determinant(){let e=this.elements,t=e[0],n=e[1],r=e[2],s=e[3],a=e[4],o=e[5],l=e[6],c=e[7],d=e[8];return t*a*d-t*o*c-n*s*d+n*o*l+r*s*c-r*a*l}invert(){let e=this.elements,t=e[0],n=e[1],r=e[2],s=e[3],a=e[4],o=e[5],l=e[6],c=e[7],d=e[8],u=d*a-o*c,h=o*l-d*s,p=c*s-a*l,g=t*u+n*h+r*p;if(g===0)return this.set(0,0,0,0,0,0,0,0,0);let x=1/g;return e[0]=u*x,e[1]=(r*c-d*n)*x,e[2]=(o*n-r*a)*x,e[3]=h*x,e[4]=(d*t-r*l)*x,e[5]=(r*s-o*t)*x,e[6]=p*x,e[7]=(n*l-c*t)*x,e[8]=(a*t-n*s)*x,this}transpose(){let e,t=this.elements;return e=t[1],t[1]=t[3],t[3]=e,e=t[2],t[2]=t[6],t[6]=e,e=t[5],t[5]=t[7],t[7]=e,this}getNormalMatrix(e){return this.setFromMatrix4(e).invert().transpose()}transposeIntoArray(e){let t=this.elements;return e[0]=t[0],e[1]=t[3],e[2]=t[6],e[3]=t[1],e[4]=t[4],e[5]=t[7],e[6]=t[2],e[7]=t[5],e[8]=t[8],this}setUvTransform(e,t,n,r,s,a,o){let l=Math.cos(s),c=Math.sin(s);return this.set(n*l,n*c,-n*(l*a+c*o)+a+e,-r*c,r*l,-r*(-c*a+l*o)+o+t,0,0,1),this}scale(e,t){return this.premultiply(Yo.makeScale(e,t)),this}rotate(e){return this.premultiply(Yo.makeRotation(-e)),this}translate(e,t){return this.premultiply(Yo.makeTranslation(e,t)),this}makeTranslation(e,t){return e.isVector2?this.set(1,0,e.x,0,1,e.y,0,0,1):this.set(1,0,e,0,1,t,0,0,1),this}makeRotation(e){let t=Math.cos(e),n=Math.sin(e);return this.set(t,-n,0,n,t,0,0,0,1),this}makeScale(e,t){return this.set(e,0,0,0,t,0,0,0,1),this}equals(e){let t=this.elements,n=e.elements;for(let r=0;r<9;r++)if(t[r]!==n[r])return!1;return!0}fromArray(e,t=0){for(let n=0;n<9;n++)this.elements[n]=e[n+t];return this}toArray(e=[],t=0){let n=this.elements;return e[t]=n[0],e[t+1]=n[1],e[t+2]=n[2],e[t+3]=n[3],e[t+4]=n[4],e[t+5]=n[5],e[t+6]=n[6],e[t+7]=n[7],e[t+8]=n[8],e}clone(){return new this.constructor().fromArray(this.elements)}},Yo=new Oe;function $l(i){for(let e=i.length-1;e>=0;--e)if(i[e]>=65535)return!0;return!1}function Vr(i){return document.createElementNS("http://www.w3.org/1999/xhtml",i)}function eu(){let i=Vr("canvas");return i.style.display="block",i}var kc={};function cr(i){i in kc||(kc[i]=!0,console.warn(i))}function tu(i,e,t){return new Promise(function(n,r){function s(){switch(i.clientWaitSync(e,i.SYNC_FLUSH_COMMANDS_BIT,0)){case i.WAIT_FAILED:r();break;case i.TIMEOUT_EXPIRED:setTimeout(s,t);break;default:n()}}setTimeout(s,t)})}var Hc=new Oe().set(.4123908,.3575843,.1804808,.212639,.7151687,.0721923,.0193308,.1191948,.9505322),Vc=new Oe().set(3.2409699,-1.5373832,-.4986108,-.9692436,1.8759675,.0415551,.0556301,-.203977,1.0569715);function Vh(){let i={enabled:!0,workingColorSpace:Si,spaces:{},convert:function(r,s,a){return this.enabled===!1||s===a||!s||!a||(this.spaces[s].transfer===Ke&&(r.r=Hn(r.r),r.g=Hn(r.g),r.b=Hn(r.b)),this.spaces[s].primaries!==this.spaces[a].primaries&&(r.applyMatrix3(this.spaces[s].toXYZ),r.applyMatrix3(this.spaces[a].fromXYZ)),this.spaces[a].transfer===Ke&&(r.r=ar(r.r),r.g=ar(r.g),r.b=ar(r.b))),r},workingToColorSpace:function(r,s){return this.convert(r,this.workingColorSpace,s)},colorSpaceToWorking:function(r,s){return this.convert(r,s,this.workingColorSpace)},getPrimaries:function(r){return this.spaces[r].primaries},getTransfer:function(r){return r===qn?kr:this.spaces[r].transfer},getToneMappingMode:function(r){return this.spaces[r].outputColorSpaceConfig.toneMappingMode||"standard"},getLuminanceCoefficients:function(r,s=this.workingColorSpace){return r.fromArray(this.spaces[s].luminanceCoefficients)},define:function(r){Object.assign(this.spaces,r)},_getMatrix:function(r,s,a){return r.copy(this.spaces[s].toXYZ).multiply(this.spaces[a].fromXYZ)},_getDrawingBufferColorSpace:function(r){return this.spaces[r].outputColorSpaceConfig.drawingBufferColorSpace},_getUnpackColorSpace:function(r=this.workingColorSpace){return this.spaces[r].workingColorSpaceConfig.unpackColorSpace},fromWorkingColorSpace:function(r,s){return cr("THREE.ColorManagement: .fromWorkingColorSpace() has been renamed to .workingToColorSpace()."),i.workingToColorSpace(r,s)},toWorkingColorSpace:function(r,s){return cr("THREE.ColorManagement: .toWorkingColorSpace() has been renamed to .colorSpaceToWorking()."),i.colorSpaceToWorking(r,s)}},e=[.64,.33,.3,.6,.15,.06],t=[.2126,.7152,.0722],n=[.3127,.329];return i.define({[Si]:{primaries:e,whitePoint:n,transfer:kr,toXYZ:Hc,fromXYZ:Vc,luminanceCoefficients:t,workingColorSpaceConfig:{unpackColorSpace:Nt},outputColorSpaceConfig:{drawingBufferColorSpace:Nt}},[Nt]:{primaries:e,whitePoint:n,transfer:Ke,toXYZ:Hc,fromXYZ:Vc,luminanceCoefficients:t,outputColorSpaceConfig:{drawingBufferColorSpace:Nt}}}),i}var $e=Vh();function Hn(i){return i<.04045?i*.0773993808:Math.pow(i*.9478672986+.0521327014,2.4)}function ar(i){return i<.0031308?i*12.92:1.055*Math.pow(i,.41666)-.055}var Gi,ha=class{static getDataURL(e,t="image/png"){if(/^data:/i.test(e.src)||typeof HTMLCanvasElement>"u")return e.src;let n;if(e instanceof HTMLCanvasElement)n=e;else{Gi===void 0&&(Gi=Vr("canvas")),Gi.width=e.width,Gi.height=e.height;let r=Gi.getContext("2d");e instanceof ImageData?r.putImageData(e,0,0):r.drawImage(e,0,0,e.width,e.height),n=Gi}return n.toDataURL(t)}static sRGBToLinear(e){if(typeof HTMLImageElement<"u"&&e instanceof HTMLImageElement||typeof HTMLCanvasElement<"u"&&e instanceof HTMLCanvasElement||typeof ImageBitmap<"u"&&e instanceof ImageBitmap){let t=Vr("canvas");t.width=e.width,t.height=e.height;let n=t.getContext("2d");n.drawImage(e,0,0,e.width,e.height);let r=n.getImageData(0,0,e.width,e.height),s=r.data;for(let a=0;a<s.length;a++)s[a]=Hn(s[a]/255)*255;return n.putImageData(r,0,0),t}else if(e.data){let t=e.data.slice(0);for(let n=0;n<t.length;n++)t instanceof Uint8Array||t instanceof Uint8ClampedArray?t[n]=Math.floor(Hn(t[n]/255)*255):t[n]=Hn(t[n]);return{data:t,width:e.width,height:e.height}}else return console.warn("THREE.ImageUtils.sRGBToLinear(): Unsupported image type. No color space conversion applied."),e}},Gh=0,dr=class{constructor(e=null){this.isSource=!0,Object.defineProperty(this,"id",{value:Gh++}),this.uuid=kn(),this.data=e,this.dataReady=!0,this.version=0}getSize(e){let t=this.data;return typeof HTMLVideoElement<"u"&&t instanceof HTMLVideoElement?e.set(t.videoWidth,t.videoHeight,0):t instanceof VideoFrame?e.set(t.displayHeight,t.displayWidth,0):t!==null?e.set(t.width,t.height,t.depth||0):e.set(0,0,0),e}set needsUpdate(e){e===!0&&this.version++}toJSON(e){let t=e===void 0||typeof e=="string";if(!t&&e.images[this.uuid]!==void 0)return e.images[this.uuid];let n={uuid:this.uuid,url:""},r=this.data;if(r!==null){let s;if(Array.isArray(r)){s=[];for(let a=0,o=r.length;a<o;a++)r[a].isDataTexture?s.push(Zo(r[a].image)):s.push(Zo(r[a]))}else s=Zo(r);n.url=s}return t||(e.images[this.uuid]=n),n}};function Zo(i){return typeof HTMLImageElement<"u"&&i instanceof HTMLImageElement||typeof HTMLCanvasElement<"u"&&i instanceof HTMLCanvasElement||typeof ImageBitmap<"u"&&i instanceof ImageBitmap?ha.getDataURL(i):i.data?{data:Array.from(i.data),width:i.width,height:i.height,type:i.data.constructor.name}:(console.warn("THREE.Texture: Unable to serialize Texture."),{})}var Wh=0,Jo=new N,Lt=class i extends Gn{constructor(e=i.DEFAULT_IMAGE,t=i.DEFAULT_MAPPING,n=ii,r=ii,s=vn,a=ui,o=un,l=Mn,c=i.DEFAULT_ANISOTROPY,d=qn){super(),this.isTexture=!0,Object.defineProperty(this,"id",{value:Wh++}),this.uuid=kn(),this.name="",this.source=new dr(e),this.mipmaps=[],this.mapping=t,this.channel=0,this.wrapS=n,this.wrapT=r,this.magFilter=s,this.minFilter=a,this.anisotropy=c,this.format=o,this.internalFormat=null,this.type=l,this.offset=new He(0,0),this.repeat=new He(1,1),this.center=new He(0,0),this.rotation=0,this.matrixAutoUpdate=!0,this.matrix=new Oe,this.generateMipmaps=!0,this.premultiplyAlpha=!1,this.flipY=!0,this.unpackAlignment=4,this.colorSpace=d,this.userData={},this.updateRanges=[],this.version=0,this.onUpdate=null,this.renderTarget=null,this.isRenderTargetTexture=!1,this.isArrayTexture=!!(e&&e.depth&&e.depth>1),this.pmremVersion=0}get width(){return this.source.getSize(Jo).x}get height(){return this.source.getSize(Jo).y}get depth(){return this.source.getSize(Jo).z}get image(){return this.source.data}set image(e=null){this.source.data=e}updateMatrix(){this.matrix.setUvTransform(this.offset.x,this.offset.y,this.repeat.x,this.repeat.y,this.rotation,this.center.x,this.center.y)}addUpdateRange(e,t){this.updateRanges.push({start:e,count:t})}clearUpdateRanges(){this.updateRanges.length=0}clone(){return new this.constructor().copy(this)}copy(e){return this.name=e.name,this.source=e.source,this.mipmaps=e.mipmaps.slice(0),this.mapping=e.mapping,this.channel=e.channel,this.wrapS=e.wrapS,this.wrapT=e.wrapT,this.magFilter=e.magFilter,this.minFilter=e.minFilter,this.anisotropy=e.anisotropy,this.format=e.format,this.internalFormat=e.internalFormat,this.type=e.type,this.offset.copy(e.offset),this.repeat.copy(e.repeat),this.center.copy(e.center),this.rotation=e.rotation,this.matrixAutoUpdate=e.matrixAutoUpdate,this.matrix.copy(e.matrix),this.generateMipmaps=e.generateMipmaps,this.premultiplyAlpha=e.premultiplyAlpha,this.flipY=e.flipY,this.unpackAlignment=e.unpackAlignment,this.colorSpace=e.colorSpace,this.renderTarget=e.renderTarget,this.isRenderTargetTexture=e.isRenderTargetTexture,this.isArrayTexture=e.isArrayTexture,this.userData=JSON.parse(JSON.stringify(e.userData)),this.needsUpdate=!0,this}setValues(e){for(let t in e){let n=e[t];if(n===void 0){console.warn(`THREE.Texture.setValues(): parameter '${t}' has value of undefined.`);continue}let r=this[t];if(r===void 0){console.warn(`THREE.Texture.setValues(): property '${t}' does not exist.`);continue}r&&n&&r.isVector2&&n.isVector2||r&&n&&r.isVector3&&n.isVector3||r&&n&&r.isMatrix3&&n.isMatrix3?r.copy(n):this[t]=n}}toJSON(e){let t=e===void 0||typeof e=="string";if(!t&&e.textures[this.uuid]!==void 0)return e.textures[this.uuid];let n={metadata:{version:4.7,type:"Texture",generator:"Texture.toJSON"},uuid:this.uuid,name:this.name,image:this.source.toJSON(e).uuid,mapping:this.mapping,channel:this.channel,repeat:[this.repeat.x,this.repeat.y],offset:[this.offset.x,this.offset.y],center:[this.center.x,this.center.y],rotation:this.rotation,wrap:[this.wrapS,this.wrapT],format:this.format,internalFormat:this.internalFormat,type:this.type,colorSpace:this.colorSpace,minFilter:this.minFilter,magFilter:this.magFilter,anisotropy:this.anisotropy,flipY:this.flipY,generateMipmaps:this.generateMipmaps,premultiplyAlpha:this.premultiplyAlpha,unpackAlignment:this.unpackAlignment};return Object.keys(this.userData).length>0&&(n.userData=this.userData),t||(e.textures[this.uuid]=n),n}dispose(){this.dispatchEvent({type:"dispose"})}transformUv(e){if(this.mapping!==Dl)return e;if(e.applyMatrix3(this.matrix),e.x<0||e.x>1)switch(this.wrapS){case la:e.x=e.x-Math.floor(e.x);break;case ii:e.x=e.x<0?0:1;break;case ca:Math.abs(Math.floor(e.x)%2)===1?e.x=Math.ceil(e.x)-e.x:e.x=e.x-Math.floor(e.x);break}if(e.y<0||e.y>1)switch(this.wrapT){case la:e.y=e.y-Math.floor(e.y);break;case ii:e.y=e.y<0?0:1;break;case ca:Math.abs(Math.floor(e.y)%2)===1?e.y=Math.ceil(e.y)-e.y:e.y=e.y-Math.floor(e.y);break}return this.flipY&&(e.y=1-e.y),e}set needsUpdate(e){e===!0&&(this.version++,this.source.needsUpdate=!0)}set needsPMREMUpdate(e){e===!0&&this.pmremVersion++}};Lt.DEFAULT_IMAGE=null;Lt.DEFAULT_MAPPING=Dl;Lt.DEFAULT_ANISOTROPY=1;var pt=class i{constructor(e=0,t=0,n=0,r=1){i.prototype.isVector4=!0,this.x=e,this.y=t,this.z=n,this.w=r}get width(){return this.z}set width(e){this.z=e}get height(){return this.w}set height(e){this.w=e}set(e,t,n,r){return this.x=e,this.y=t,this.z=n,this.w=r,this}setScalar(e){return this.x=e,this.y=e,this.z=e,this.w=e,this}setX(e){return this.x=e,this}setY(e){return this.y=e,this}setZ(e){return this.z=e,this}setW(e){return this.w=e,this}setComponent(e,t){switch(e){case 0:this.x=t;break;case 1:this.y=t;break;case 2:this.z=t;break;case 3:this.w=t;break;default:throw new Error("index is out of range: "+e)}return this}getComponent(e){switch(e){case 0:return this.x;case 1:return this.y;case 2:return this.z;case 3:return this.w;default:throw new Error("index is out of range: "+e)}}clone(){return new this.constructor(this.x,this.y,this.z,this.w)}copy(e){return this.x=e.x,this.y=e.y,this.z=e.z,this.w=e.w!==void 0?e.w:1,this}add(e){return this.x+=e.x,this.y+=e.y,this.z+=e.z,this.w+=e.w,this}addScalar(e){return this.x+=e,this.y+=e,this.z+=e,this.w+=e,this}addVectors(e,t){return this.x=e.x+t.x,this.y=e.y+t.y,this.z=e.z+t.z,this.w=e.w+t.w,this}addScaledVector(e,t){return this.x+=e.x*t,this.y+=e.y*t,this.z+=e.z*t,this.w+=e.w*t,this}sub(e){return this.x-=e.x,this.y-=e.y,this.z-=e.z,this.w-=e.w,this}subScalar(e){return this.x-=e,this.y-=e,this.z-=e,this.w-=e,this}subVectors(e,t){return this.x=e.x-t.x,this.y=e.y-t.y,this.z=e.z-t.z,this.w=e.w-t.w,this}multiply(e){return this.x*=e.x,this.y*=e.y,this.z*=e.z,this.w*=e.w,this}multiplyScalar(e){return this.x*=e,this.y*=e,this.z*=e,this.w*=e,this}applyMatrix4(e){let t=this.x,n=this.y,r=this.z,s=this.w,a=e.elements;return this.x=a[0]*t+a[4]*n+a[8]*r+a[12]*s,this.y=a[1]*t+a[5]*n+a[9]*r+a[13]*s,this.z=a[2]*t+a[6]*n+a[10]*r+a[14]*s,this.w=a[3]*t+a[7]*n+a[11]*r+a[15]*s,this}divide(e){return this.x/=e.x,this.y/=e.y,this.z/=e.z,this.w/=e.w,this}divideScalar(e){return this.multiplyScalar(1/e)}setAxisAngleFromQuaternion(e){this.w=2*Math.acos(e.w);let t=Math.sqrt(1-e.w*e.w);return t<1e-4?(this.x=1,this.y=0,this.z=0):(this.x=e.x/t,this.y=e.y/t,this.z=e.z/t),this}setAxisAngleFromRotationMatrix(e){let t,n,r,s,l=e.elements,c=l[0],d=l[4],u=l[8],h=l[1],p=l[5],g=l[9],x=l[2],m=l[6],f=l[10];if(Math.abs(d-h)<.01&&Math.abs(u-x)<.01&&Math.abs(g-m)<.01){if(Math.abs(d+h)<.1&&Math.abs(u+x)<.1&&Math.abs(g+m)<.1&&Math.abs(c+p+f-3)<.1)return this.set(1,0,0,0),this;t=Math.PI;let M=(c+1)/2,y=(p+1)/2,C=(f+1)/2,E=(d+h)/4,R=(u+x)/4,P=(g+m)/4;return M>y&&M>C?M<.01?(n=0,r=.707106781,s=.707106781):(n=Math.sqrt(M),r=E/n,s=R/n):y>C?y<.01?(n=.707106781,r=0,s=.707106781):(r=Math.sqrt(y),n=E/r,s=P/r):C<.01?(n=.707106781,r=.707106781,s=0):(s=Math.sqrt(C),n=R/s,r=P/s),this.set(n,r,s,t),this}let S=Math.sqrt((m-g)*(m-g)+(u-x)*(u-x)+(h-d)*(h-d));return Math.abs(S)<.001&&(S=1),this.x=(m-g)/S,this.y=(u-x)/S,this.z=(h-d)/S,this.w=Math.acos((c+p+f-1)/2),this}setFromMatrixPosition(e){let t=e.elements;return this.x=t[12],this.y=t[13],this.z=t[14],this.w=t[15],this}min(e){return this.x=Math.min(this.x,e.x),this.y=Math.min(this.y,e.y),this.z=Math.min(this.z,e.z),this.w=Math.min(this.w,e.w),this}max(e){return this.x=Math.max(this.x,e.x),this.y=Math.max(this.y,e.y),this.z=Math.max(this.z,e.z),this.w=Math.max(this.w,e.w),this}clamp(e,t){return this.x=Ge(this.x,e.x,t.x),this.y=Ge(this.y,e.y,t.y),this.z=Ge(this.z,e.z,t.z),this.w=Ge(this.w,e.w,t.w),this}clampScalar(e,t){return this.x=Ge(this.x,e,t),this.y=Ge(this.y,e,t),this.z=Ge(this.z,e,t),this.w=Ge(this.w,e,t),this}clampLength(e,t){let n=this.length();return this.divideScalar(n||1).multiplyScalar(Ge(n,e,t))}floor(){return this.x=Math.floor(this.x),this.y=Math.floor(this.y),this.z=Math.floor(this.z),this.w=Math.floor(this.w),this}ceil(){return this.x=Math.ceil(this.x),this.y=Math.ceil(this.y),this.z=Math.ceil(this.z),this.w=Math.ceil(this.w),this}round(){return this.x=Math.round(this.x),this.y=Math.round(this.y),this.z=Math.round(this.z),this.w=Math.round(this.w),this}roundToZero(){return this.x=Math.trunc(this.x),this.y=Math.trunc(this.y),this.z=Math.trunc(this.z),this.w=Math.trunc(this.w),this}negate(){return this.x=-this.x,this.y=-this.y,this.z=-this.z,this.w=-this.w,this}dot(e){return this.x*e.x+this.y*e.y+this.z*e.z+this.w*e.w}lengthSq(){return this.x*this.x+this.y*this.y+this.z*this.z+this.w*this.w}length(){return Math.sqrt(this.x*this.x+this.y*this.y+this.z*this.z+this.w*this.w)}manhattanLength(){return Math.abs(this.x)+Math.abs(this.y)+Math.abs(this.z)+Math.abs(this.w)}normalize(){return this.divideScalar(this.length()||1)}setLength(e){return this.normalize().multiplyScalar(e)}lerp(e,t){return this.x+=(e.x-this.x)*t,this.y+=(e.y-this.y)*t,this.z+=(e.z-this.z)*t,this.w+=(e.w-this.w)*t,this}lerpVectors(e,t,n){return this.x=e.x+(t.x-e.x)*n,this.y=e.y+(t.y-e.y)*n,this.z=e.z+(t.z-e.z)*n,this.w=e.w+(t.w-e.w)*n,this}equals(e){return e.x===this.x&&e.y===this.y&&e.z===this.z&&e.w===this.w}fromArray(e,t=0){return this.x=e[t],this.y=e[t+1],this.z=e[t+2],this.w=e[t+3],this}toArray(e=[],t=0){return e[t]=this.x,e[t+1]=this.y,e[t+2]=this.z,e[t+3]=this.w,e}fromBufferAttribute(e,t){return this.x=e.getX(t),this.y=e.getY(t),this.z=e.getZ(t),this.w=e.getW(t),this}random(){return this.x=Math.random(),this.y=Math.random(),this.z=Math.random(),this.w=Math.random(),this}*[Symbol.iterator](){yield this.x,yield this.y,yield this.z,yield this.w}},fa=class extends Gn{constructor(e=1,t=1,n={}){super(),n=Object.assign({generateMipmaps:!1,internalFormat:null,minFilter:vn,depthBuffer:!0,stencilBuffer:!1,resolveDepthBuffer:!0,resolveStencilBuffer:!0,depthTexture:null,samples:0,count:1,depth:1,multiview:!1},n),this.isRenderTarget=!0,this.width=e,this.height=t,this.depth=n.depth,this.scissor=new pt(0,0,e,t),this.scissorTest=!1,this.viewport=new pt(0,0,e,t);let r={width:e,height:t,depth:n.depth},s=new Lt(r);this.textures=[];let a=n.count;for(let o=0;o<a;o++)this.textures[o]=s.clone(),this.textures[o].isRenderTargetTexture=!0,this.textures[o].renderTarget=this;this._setTextureOptions(n),this.depthBuffer=n.depthBuffer,this.stencilBuffer=n.stencilBuffer,this.resolveDepthBuffer=n.resolveDepthBuffer,this.resolveStencilBuffer=n.resolveStencilBuffer,this._depthTexture=null,this.depthTexture=n.depthTexture,this.samples=n.samples,this.multiview=n.multiview}_setTextureOptions(e={}){let t={minFilter:vn,generateMipmaps:!1,flipY:!1,internalFormat:null};e.mapping!==void 0&&(t.mapping=e.mapping),e.wrapS!==void 0&&(t.wrapS=e.wrapS),e.wrapT!==void 0&&(t.wrapT=e.wrapT),e.wrapR!==void 0&&(t.wrapR=e.wrapR),e.magFilter!==void 0&&(t.magFilter=e.magFilter),e.minFilter!==void 0&&(t.minFilter=e.minFilter),e.format!==void 0&&(t.format=e.format),e.type!==void 0&&(t.type=e.type),e.anisotropy!==void 0&&(t.anisotropy=e.anisotropy),e.colorSpace!==void 0&&(t.colorSpace=e.colorSpace),e.flipY!==void 0&&(t.flipY=e.flipY),e.generateMipmaps!==void 0&&(t.generateMipmaps=e.generateMipmaps),e.internalFormat!==void 0&&(t.internalFormat=e.internalFormat);for(let n=0;n<this.textures.length;n++)this.textures[n].setValues(t)}get texture(){return this.textures[0]}set texture(e){this.textures[0]=e}set depthTexture(e){this._depthTexture!==null&&(this._depthTexture.renderTarget=null),e!==null&&(e.renderTarget=this),this._depthTexture=e}get depthTexture(){return this._depthTexture}setSize(e,t,n=1){if(this.width!==e||this.height!==t||this.depth!==n){this.width=e,this.height=t,this.depth=n;for(let r=0,s=this.textures.length;r<s;r++)this.textures[r].image.width=e,this.textures[r].image.height=t,this.textures[r].image.depth=n,this.textures[r].isArrayTexture=this.textures[r].image.depth>1;this.dispose()}this.viewport.set(0,0,e,t),this.scissor.set(0,0,e,t)}clone(){return new this.constructor().copy(this)}copy(e){this.width=e.width,this.height=e.height,this.depth=e.depth,this.scissor.copy(e.scissor),this.scissorTest=e.scissorTest,this.viewport.copy(e.viewport),this.textures.length=0;for(let t=0,n=e.textures.length;t<n;t++){this.textures[t]=e.textures[t].clone(),this.textures[t].isRenderTargetTexture=!0,this.textures[t].renderTarget=this;let r=Object.assign({},e.textures[t].image);this.textures[t].source=new dr(r)}return this.depthBuffer=e.depthBuffer,this.stencilBuffer=e.stencilBuffer,this.resolveDepthBuffer=e.resolveDepthBuffer,this.resolveStencilBuffer=e.resolveStencilBuffer,e.depthTexture!==null&&(this.depthTexture=e.depthTexture.clone()),this.samples=e.samples,this}dispose(){this.dispatchEvent({type:"dispose"})}},Cn=class extends fa{constructor(e=1,t=1,n={}){super(e,t,n),this.isWebGLRenderTarget=!0}},Gr=class extends Lt{constructor(e=null,t=1,n=1,r=1){super(null),this.isDataArrayTexture=!0,this.image={data:e,width:t,height:n,depth:r},this.magFilter=cn,this.minFilter=cn,this.wrapR=ii,this.generateMipmaps=!1,this.flipY=!1,this.unpackAlignment=1,this.layerUpdates=new Set}addLayerUpdate(e){this.layerUpdates.add(e)}clearLayerUpdates(){this.layerUpdates.clear()}};var pa=class extends Lt{constructor(e=null,t=1,n=1,r=1){super(null),this.isData3DTexture=!0,this.image={data:e,width:t,height:n,depth:r},this.magFilter=cn,this.minFilter=cn,this.wrapR=ii,this.generateMipmaps=!1,this.flipY=!1,this.unpackAlignment=1}};var si=class{constructor(e=new N(1/0,1/0,1/0),t=new N(-1/0,-1/0,-1/0)){this.isBox3=!0,this.min=e,this.max=t}set(e,t){return this.min.copy(e),this.max.copy(t),this}setFromArray(e){this.makeEmpty();for(let t=0,n=e.length;t<n;t+=3)this.expandByPoint(mn.fromArray(e,t));return this}setFromBufferAttribute(e){this.makeEmpty();for(let t=0,n=e.count;t<n;t++)this.expandByPoint(mn.fromBufferAttribute(e,t));return this}setFromPoints(e){this.makeEmpty();for(let t=0,n=e.length;t<n;t++)this.expandByPoint(e[t]);return this}setFromCenterAndSize(e,t){let n=mn.copy(t).multiplyScalar(.5);return this.min.copy(e).sub(n),this.max.copy(e).add(n),this}setFromObject(e,t=!1){return this.makeEmpty(),this.expandByObject(e,t)}clone(){return new this.constructor().copy(this)}copy(e){return this.min.copy(e.min),this.max.copy(e.max),this}makeEmpty(){return this.min.x=this.min.y=this.min.z=1/0,this.max.x=this.max.y=this.max.z=-1/0,this}isEmpty(){return this.max.x<this.min.x||this.max.y<this.min.y||this.max.z<this.min.z}getCenter(e){return this.isEmpty()?e.set(0,0,0):e.addVectors(this.min,this.max).multiplyScalar(.5)}getSize(e){return this.isEmpty()?e.set(0,0,0):e.subVectors(this.max,this.min)}expandByPoint(e){return this.min.min(e),this.max.max(e),this}expandByVector(e){return this.min.sub(e),this.max.add(e),this}expandByScalar(e){return this.min.addScalar(-e),this.max.addScalar(e),this}expandByObject(e,t=!1){e.updateWorldMatrix(!1,!1);let n=e.geometry;if(n!==void 0){let s=n.getAttribute("position");if(t===!0&&s!==void 0&&e.isInstancedMesh!==!0)for(let a=0,o=s.count;a<o;a++)e.isMesh===!0?e.getVertexPosition(a,mn):mn.fromBufferAttribute(s,a),mn.applyMatrix4(e.matrixWorld),this.expandByPoint(mn);else e.boundingBox!==void 0?(e.boundingBox===null&&e.computeBoundingBox(),Is.copy(e.boundingBox)):(n.boundingBox===null&&n.computeBoundingBox(),Is.copy(n.boundingBox)),Is.applyMatrix4(e.matrixWorld),this.union(Is)}let r=e.children;for(let s=0,a=r.length;s<a;s++)this.expandByObject(r[s],t);return this}containsPoint(e){return e.x>=this.min.x&&e.x<=this.max.x&&e.y>=this.min.y&&e.y<=this.max.y&&e.z>=this.min.z&&e.z<=this.max.z}containsBox(e){return this.min.x<=e.min.x&&e.max.x<=this.max.x&&this.min.y<=e.min.y&&e.max.y<=this.max.y&&this.min.z<=e.min.z&&e.max.z<=this.max.z}getParameter(e,t){return t.set((e.x-this.min.x)/(this.max.x-this.min.x),(e.y-this.min.y)/(this.max.y-this.min.y),(e.z-this.min.z)/(this.max.z-this.min.z))}intersectsBox(e){return e.max.x>=this.min.x&&e.min.x<=this.max.x&&e.max.y>=this.min.y&&e.min.y<=this.max.y&&e.max.z>=this.min.z&&e.min.z<=this.max.z}intersectsSphere(e){return this.clampPoint(e.center,mn),mn.distanceToSquared(e.center)<=e.radius*e.radius}intersectsPlane(e){let t,n;return e.normal.x>0?(t=e.normal.x*this.min.x,n=e.normal.x*this.max.x):(t=e.normal.x*this.max.x,n=e.normal.x*this.min.x),e.normal.y>0?(t+=e.normal.y*this.min.y,n+=e.normal.y*this.max.y):(t+=e.normal.y*this.max.y,n+=e.normal.y*this.min.y),e.normal.z>0?(t+=e.normal.z*this.min.z,n+=e.normal.z*this.max.z):(t+=e.normal.z*this.max.z,n+=e.normal.z*this.min.z),t<=-e.constant&&n>=-e.constant}intersectsTriangle(e){if(this.isEmpty())return!1;this.getCenter(Ir),Ps.subVectors(this.max,Ir),Wi.subVectors(e.a,Ir),Xi.subVectors(e.b,Ir),$i.subVectors(e.c,Ir),Kn.subVectors(Xi,Wi),jn.subVectors($i,Xi),xi.subVectors(Wi,$i);let t=[0,-Kn.z,Kn.y,0,-jn.z,jn.y,0,-xi.z,xi.y,Kn.z,0,-Kn.x,jn.z,0,-jn.x,xi.z,0,-xi.x,-Kn.y,Kn.x,0,-jn.y,jn.x,0,-xi.y,xi.x,0];return!Ko(t,Wi,Xi,$i,Ps)||(t=[1,0,0,0,1,0,0,0,1],!Ko(t,Wi,Xi,$i,Ps))?!1:(Ns.crossVectors(Kn,jn),t=[Ns.x,Ns.y,Ns.z],Ko(t,Wi,Xi,$i,Ps))}clampPoint(e,t){return t.copy(e).clamp(this.min,this.max)}distanceToPoint(e){return this.clampPoint(e,mn).distanceTo(e)}getBoundingSphere(e){return this.isEmpty()?e.makeEmpty():(this.getCenter(e.center),e.radius=this.getSize(mn).length()*.5),e}intersect(e){return this.min.max(e.min),this.max.min(e.max),this.isEmpty()&&this.makeEmpty(),this}union(e){return this.min.min(e.min),this.max.max(e.max),this}applyMatrix4(e){return this.isEmpty()?this:(Fn[0].set(this.min.x,this.min.y,this.min.z).applyMatrix4(e),Fn[1].set(this.min.x,this.min.y,this.max.z).applyMatrix4(e),Fn[2].set(this.min.x,this.max.y,this.min.z).applyMatrix4(e),Fn[3].set(this.min.x,this.max.y,this.max.z).applyMatrix4(e),Fn[4].set(this.max.x,this.min.y,this.min.z).applyMatrix4(e),Fn[5].set(this.max.x,this.min.y,this.max.z).applyMatrix4(e),Fn[6].set(this.max.x,this.max.y,this.min.z).applyMatrix4(e),Fn[7].set(this.max.x,this.max.y,this.max.z).applyMatrix4(e),this.setFromPoints(Fn),this)}translate(e){return this.min.add(e),this.max.add(e),this}equals(e){return e.min.equals(this.min)&&e.max.equals(this.max)}toJSON(){return{min:this.min.toArray(),max:this.max.toArray()}}fromJSON(e){return this.min.fromArray(e.min),this.max.fromArray(e.max),this}},Fn=[new N,new N,new N,new N,new N,new N,new N,new N],mn=new N,Is=new si,Wi=new N,Xi=new N,$i=new N,Kn=new N,jn=new N,xi=new N,Ir=new N,Ps=new N,Ns=new N,_i=new N;function Ko(i,e,t,n,r){for(let s=0,a=i.length-3;s<=a;s+=3){_i.fromArray(i,s);let o=r.x*Math.abs(_i.x)+r.y*Math.abs(_i.y)+r.z*Math.abs(_i.z),l=e.dot(_i),c=t.dot(_i),d=n.dot(_i);if(Math.max(-Math.max(l,c,d),Math.min(l,c,d))>o)return!1}return!0}var Xh=new si,Pr=new N,jo=new N,ai=class{constructor(e=new N,t=-1){this.isSphere=!0,this.center=e,this.radius=t}set(e,t){return this.center.copy(e),this.radius=t,this}setFromPoints(e,t){let n=this.center;t!==void 0?n.copy(t):Xh.setFromPoints(e).getCenter(n);let r=0;for(let s=0,a=e.length;s<a;s++)r=Math.max(r,n.distanceToSquared(e[s]));return this.radius=Math.sqrt(r),this}copy(e){return this.center.copy(e.center),this.radius=e.radius,this}isEmpty(){return this.radius<0}makeEmpty(){return this.center.set(0,0,0),this.radius=-1,this}containsPoint(e){return e.distanceToSquared(this.center)<=this.radius*this.radius}distanceToPoint(e){return e.distanceTo(this.center)-this.radius}intersectsSphere(e){let t=this.radius+e.radius;return e.center.distanceToSquared(this.center)<=t*t}intersectsBox(e){return e.intersectsSphere(this)}intersectsPlane(e){return Math.abs(e.distanceToPoint(this.center))<=this.radius}clampPoint(e,t){let n=this.center.distanceToSquared(e);return t.copy(e),n>this.radius*this.radius&&(t.sub(this.center).normalize(),t.multiplyScalar(this.radius).add(this.center)),t}getBoundingBox(e){return this.isEmpty()?(e.makeEmpty(),e):(e.set(this.center,this.center),e.expandByScalar(this.radius),e)}applyMatrix4(e){return this.center.applyMatrix4(e),this.radius=this.radius*e.getMaxScaleOnAxis(),this}translate(e){return this.center.add(e),this}expandByPoint(e){if(this.isEmpty())return this.center.copy(e),this.radius=0,this;Pr.subVectors(e,this.center);let t=Pr.lengthSq();if(t>this.radius*this.radius){let n=Math.sqrt(t),r=(n-this.radius)*.5;this.center.addScaledVector(Pr,r/n),this.radius+=r}return this}union(e){return e.isEmpty()?this:this.isEmpty()?(this.copy(e),this):(this.center.equals(e.center)===!0?this.radius=Math.max(this.radius,e.radius):(jo.subVectors(e.center,this.center).setLength(e.radius),this.expandByPoint(Pr.copy(e.center).add(jo)),this.expandByPoint(Pr.copy(e.center).sub(jo))),this)}equals(e){return e.center.equals(this.center)&&e.radius===this.radius}clone(){return new this.constructor().copy(this)}toJSON(){return{radius:this.radius,center:this.center.toArray()}}fromJSON(e){return this.radius=e.radius,this.center.fromArray(e.center),this}},Un=new N,Qo=new N,Ds=new N,Qn=new N,el=new N,Ls=new N,tl=new N,ur=class{constructor(e=new N,t=new N(0,0,-1)){this.origin=e,this.direction=t}set(e,t){return this.origin.copy(e),this.direction.copy(t),this}copy(e){return this.origin.copy(e.origin),this.direction.copy(e.direction),this}at(e,t){return t.copy(this.origin).addScaledVector(this.direction,e)}lookAt(e){return this.direction.copy(e).sub(this.origin).normalize(),this}recast(e){return this.origin.copy(this.at(e,Un)),this}closestPointToPoint(e,t){t.subVectors(e,this.origin);let n=t.dot(this.direction);return n<0?t.copy(this.origin):t.copy(this.origin).addScaledVector(this.direction,n)}distanceToPoint(e){return Math.sqrt(this.distanceSqToPoint(e))}distanceSqToPoint(e){let t=Un.subVectors(e,this.origin).dot(this.direction);return t<0?this.origin.distanceToSquared(e):(Un.copy(this.origin).addScaledVector(this.direction,t),Un.distanceToSquared(e))}distanceSqToSegment(e,t,n,r){Qo.copy(e).add(t).multiplyScalar(.5),Ds.copy(t).sub(e).normalize(),Qn.copy(this.origin).sub(Qo);let s=e.distanceTo(t)*.5,a=-this.direction.dot(Ds),o=Qn.dot(this.direction),l=-Qn.dot(Ds),c=Qn.lengthSq(),d=Math.abs(1-a*a),u,h,p,g;if(d>0)if(u=a*l-o,h=a*o-l,g=s*d,u>=0)if(h>=-g)if(h<=g){let x=1/d;u*=x,h*=x,p=u*(u+a*h+2*o)+h*(a*u+h+2*l)+c}else h=s,u=Math.max(0,-(a*h+o)),p=-u*u+h*(h+2*l)+c;else h=-s,u=Math.max(0,-(a*h+o)),p=-u*u+h*(h+2*l)+c;else h<=-g?(u=Math.max(0,-(-a*s+o)),h=u>0?-s:Math.min(Math.max(-s,-l),s),p=-u*u+h*(h+2*l)+c):h<=g?(u=0,h=Math.min(Math.max(-s,-l),s),p=h*(h+2*l)+c):(u=Math.max(0,-(a*s+o)),h=u>0?s:Math.min(Math.max(-s,-l),s),p=-u*u+h*(h+2*l)+c);else h=a>0?-s:s,u=Math.max(0,-(a*h+o)),p=-u*u+h*(h+2*l)+c;return n&&n.copy(this.origin).addScaledVector(this.direction,u),r&&r.copy(Qo).addScaledVector(Ds,h),p}intersectSphere(e,t){Un.subVectors(e.center,this.origin);let n=Un.dot(this.direction),r=Un.dot(Un)-n*n,s=e.radius*e.radius;if(r>s)return null;let a=Math.sqrt(s-r),o=n-a,l=n+a;return l<0?null:o<0?this.at(l,t):this.at(o,t)}intersectsSphere(e){return e.radius<0?!1:this.distanceSqToPoint(e.center)<=e.radius*e.radius}distanceToPlane(e){let t=e.normal.dot(this.direction);if(t===0)return e.distanceToPoint(this.origin)===0?0:null;let n=-(this.origin.dot(e.normal)+e.constant)/t;return n>=0?n:null}intersectPlane(e,t){let n=this.distanceToPlane(e);return n===null?null:this.at(n,t)}intersectsPlane(e){let t=e.distanceToPoint(this.origin);return t===0||e.normal.dot(this.direction)*t<0}intersectBox(e,t){let n,r,s,a,o,l,c=1/this.direction.x,d=1/this.direction.y,u=1/this.direction.z,h=this.origin;return c>=0?(n=(e.min.x-h.x)*c,r=(e.max.x-h.x)*c):(n=(e.max.x-h.x)*c,r=(e.min.x-h.x)*c),d>=0?(s=(e.min.y-h.y)*d,a=(e.max.y-h.y)*d):(s=(e.max.y-h.y)*d,a=(e.min.y-h.y)*d),n>a||s>r||((s>n||isNaN(n))&&(n=s),(a<r||isNaN(r))&&(r=a),u>=0?(o=(e.min.z-h.z)*u,l=(e.max.z-h.z)*u):(o=(e.max.z-h.z)*u,l=(e.min.z-h.z)*u),n>l||o>r)||((o>n||n!==n)&&(n=o),(l<r||r!==r)&&(r=l),r<0)?null:this.at(n>=0?n:r,t)}intersectsBox(e){return this.intersectBox(e,Un)!==null}intersectTriangle(e,t,n,r,s){el.subVectors(t,e),Ls.subVectors(n,e),tl.crossVectors(el,Ls);let a=this.direction.dot(tl),o;if(a>0){if(r)return null;o=1}else if(a<0)o=-1,a=-a;else return null;Qn.subVectors(this.origin,e);let l=o*this.direction.dot(Ls.crossVectors(Qn,Ls));if(l<0)return null;let c=o*this.direction.dot(el.cross(Qn));if(c<0||l+c>a)return null;let d=-o*Qn.dot(tl);return d<0?null:this.at(d/a,s)}applyMatrix4(e){return this.origin.applyMatrix4(e),this.direction.transformDirection(e),this}equals(e){return e.origin.equals(this.origin)&&e.direction.equals(this.direction)}clone(){return new this.constructor().copy(this)}},ct=class i{constructor(e,t,n,r,s,a,o,l,c,d,u,h,p,g,x,m){i.prototype.isMatrix4=!0,this.elements=[1,0,0,0,0,1,0,0,0,0,1,0,0,0,0,1],e!==void 0&&this.set(e,t,n,r,s,a,o,l,c,d,u,h,p,g,x,m)}set(e,t,n,r,s,a,o,l,c,d,u,h,p,g,x,m){let f=this.elements;return f[0]=e,f[4]=t,f[8]=n,f[12]=r,f[1]=s,f[5]=a,f[9]=o,f[13]=l,f[2]=c,f[6]=d,f[10]=u,f[14]=h,f[3]=p,f[7]=g,f[11]=x,f[15]=m,this}identity(){return this.set(1,0,0,0,0,1,0,0,0,0,1,0,0,0,0,1),this}clone(){return new i().fromArray(this.elements)}copy(e){let t=this.elements,n=e.elements;return t[0]=n[0],t[1]=n[1],t[2]=n[2],t[3]=n[3],t[4]=n[4],t[5]=n[5],t[6]=n[6],t[7]=n[7],t[8]=n[8],t[9]=n[9],t[10]=n[10],t[11]=n[11],t[12]=n[12],t[13]=n[13],t[14]=n[14],t[15]=n[15],this}copyPosition(e){let t=this.elements,n=e.elements;return t[12]=n[12],t[13]=n[13],t[14]=n[14],this}setFromMatrix3(e){let t=e.elements;return this.set(t[0],t[3],t[6],0,t[1],t[4],t[7],0,t[2],t[5],t[8],0,0,0,0,1),this}extractBasis(e,t,n){return e.setFromMatrixColumn(this,0),t.setFromMatrixColumn(this,1),n.setFromMatrixColumn(this,2),this}makeBasis(e,t,n){return this.set(e.x,t.x,n.x,0,e.y,t.y,n.y,0,e.z,t.z,n.z,0,0,0,0,1),this}extractRotation(e){let t=this.elements,n=e.elements,r=1/qi.setFromMatrixColumn(e,0).length(),s=1/qi.setFromMatrixColumn(e,1).length(),a=1/qi.setFromMatrixColumn(e,2).length();return t[0]=n[0]*r,t[1]=n[1]*r,t[2]=n[2]*r,t[3]=0,t[4]=n[4]*s,t[5]=n[5]*s,t[6]=n[6]*s,t[7]=0,t[8]=n[8]*a,t[9]=n[9]*a,t[10]=n[10]*a,t[11]=0,t[12]=0,t[13]=0,t[14]=0,t[15]=1,this}makeRotationFromEuler(e){let t=this.elements,n=e.x,r=e.y,s=e.z,a=Math.cos(n),o=Math.sin(n),l=Math.cos(r),c=Math.sin(r),d=Math.cos(s),u=Math.sin(s);if(e.order==="XYZ"){let h=a*d,p=a*u,g=o*d,x=o*u;t[0]=l*d,t[4]=-l*u,t[8]=c,t[1]=p+g*c,t[5]=h-x*c,t[9]=-o*l,t[2]=x-h*c,t[6]=g+p*c,t[10]=a*l}else if(e.order==="YXZ"){let h=l*d,p=l*u,g=c*d,x=c*u;t[0]=h+x*o,t[4]=g*o-p,t[8]=a*c,t[1]=a*u,t[5]=a*d,t[9]=-o,t[2]=p*o-g,t[6]=x+h*o,t[10]=a*l}else if(e.order==="ZXY"){let h=l*d,p=l*u,g=c*d,x=c*u;t[0]=h-x*o,t[4]=-a*u,t[8]=g+p*o,t[1]=p+g*o,t[5]=a*d,t[9]=x-h*o,t[2]=-a*c,t[6]=o,t[10]=a*l}else if(e.order==="ZYX"){let h=a*d,p=a*u,g=o*d,x=o*u;t[0]=l*d,t[4]=g*c-p,t[8]=h*c+x,t[1]=l*u,t[5]=x*c+h,t[9]=p*c-g,t[2]=-c,t[6]=o*l,t[10]=a*l}else if(e.order==="YZX"){let h=a*l,p=a*c,g=o*l,x=o*c;t[0]=l*d,t[4]=x-h*u,t[8]=g*u+p,t[1]=u,t[5]=a*d,t[9]=-o*d,t[2]=-c*d,t[6]=p*u+g,t[10]=h-x*u}else if(e.order==="XZY"){let h=a*l,p=a*c,g=o*l,x=o*c;t[0]=l*d,t[4]=-u,t[8]=c*d,t[1]=h*u+x,t[5]=a*d,t[9]=p*u-g,t[2]=g*u-p,t[6]=o*d,t[10]=x*u+h}return t[3]=0,t[7]=0,t[11]=0,t[12]=0,t[13]=0,t[14]=0,t[15]=1,this}makeRotationFromQuaternion(e){return this.compose($h,e,qh)}lookAt(e,t,n){let r=this.elements;return jt.subVectors(e,t),jt.lengthSq()===0&&(jt.z=1),jt.normalize(),ei.crossVectors(n,jt),ei.lengthSq()===0&&(Math.abs(n.z)===1?jt.x+=1e-4:jt.z+=1e-4,jt.normalize(),ei.crossVectors(n,jt)),ei.normalize(),Fs.crossVectors(jt,ei),r[0]=ei.x,r[4]=Fs.x,r[8]=jt.x,r[1]=ei.y,r[5]=Fs.y,r[9]=jt.y,r[2]=ei.z,r[6]=Fs.z,r[10]=jt.z,this}multiply(e){return this.multiplyMatrices(this,e)}premultiply(e){return this.multiplyMatrices(e,this)}multiplyMatrices(e,t){let n=e.elements,r=t.elements,s=this.elements,a=n[0],o=n[4],l=n[8],c=n[12],d=n[1],u=n[5],h=n[9],p=n[13],g=n[2],x=n[6],m=n[10],f=n[14],S=n[3],M=n[7],y=n[11],C=n[15],E=r[0],R=r[4],P=r[8],w=r[12],v=r[1],T=r[5],D=r[9],F=r[13],B=r[2],k=r[6],W=r[10],X=r[14],H=r[3],Q=r[7],ne=r[11],fe=r[15];return s[0]=a*E+o*v+l*B+c*H,s[4]=a*R+o*T+l*k+c*Q,s[8]=a*P+o*D+l*W+c*ne,s[12]=a*w+o*F+l*X+c*fe,s[1]=d*E+u*v+h*B+p*H,s[5]=d*R+u*T+h*k+p*Q,s[9]=d*P+u*D+h*W+p*ne,s[13]=d*w+u*F+h*X+p*fe,s[2]=g*E+x*v+m*B+f*H,s[6]=g*R+x*T+m*k+f*Q,s[10]=g*P+x*D+m*W+f*ne,s[14]=g*w+x*F+m*X+f*fe,s[3]=S*E+M*v+y*B+C*H,s[7]=S*R+M*T+y*k+C*Q,s[11]=S*P+M*D+y*W+C*ne,s[15]=S*w+M*F+y*X+C*fe,this}multiplyScalar(e){let t=this.elements;return t[0]*=e,t[4]*=e,t[8]*=e,t[12]*=e,t[1]*=e,t[5]*=e,t[9]*=e,t[13]*=e,t[2]*=e,t[6]*=e,t[10]*=e,t[14]*=e,t[3]*=e,t[7]*=e,t[11]*=e,t[15]*=e,this}determinant(){let e=this.elements,t=e[0],n=e[4],r=e[8],s=e[12],a=e[1],o=e[5],l=e[9],c=e[13],d=e[2],u=e[6],h=e[10],p=e[14],g=e[3],x=e[7],m=e[11],f=e[15];return g*(+s*l*u-r*c*u-s*o*h+n*c*h+r*o*p-n*l*p)+x*(+t*l*p-t*c*h+s*a*h-r*a*p+r*c*d-s*l*d)+m*(+t*c*u-t*o*p-s*a*u+n*a*p+s*o*d-n*c*d)+f*(-r*o*d-t*l*u+t*o*h+r*a*u-n*a*h+n*l*d)}transpose(){let e=this.elements,t;return t=e[1],e[1]=e[4],e[4]=t,t=e[2],e[2]=e[8],e[8]=t,t=e[6],e[6]=e[9],e[9]=t,t=e[3],e[3]=e[12],e[12]=t,t=e[7],e[7]=e[13],e[13]=t,t=e[11],e[11]=e[14],e[14]=t,this}setPosition(e,t,n){let r=this.elements;return e.isVector3?(r[12]=e.x,r[13]=e.y,r[14]=e.z):(r[12]=e,r[13]=t,r[14]=n),this}invert(){let e=this.elements,t=e[0],n=e[1],r=e[2],s=e[3],a=e[4],o=e[5],l=e[6],c=e[7],d=e[8],u=e[9],h=e[10],p=e[11],g=e[12],x=e[13],m=e[14],f=e[15],S=u*m*c-x*h*c+x*l*p-o*m*p-u*l*f+o*h*f,M=g*h*c-d*m*c-g*l*p+a*m*p+d*l*f-a*h*f,y=d*x*c-g*u*c+g*o*p-a*x*p-d*o*f+a*u*f,C=g*u*l-d*x*l-g*o*h+a*x*h+d*o*m-a*u*m,E=t*S+n*M+r*y+s*C;if(E===0)return this.set(0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0);let R=1/E;return e[0]=S*R,e[1]=(x*h*s-u*m*s-x*r*p+n*m*p+u*r*f-n*h*f)*R,e[2]=(o*m*s-x*l*s+x*r*c-n*m*c-o*r*f+n*l*f)*R,e[3]=(u*l*s-o*h*s-u*r*c+n*h*c+o*r*p-n*l*p)*R,e[4]=M*R,e[5]=(d*m*s-g*h*s+g*r*p-t*m*p-d*r*f+t*h*f)*R,e[6]=(g*l*s-a*m*s-g*r*c+t*m*c+a*r*f-t*l*f)*R,e[7]=(a*h*s-d*l*s+d*r*c-t*h*c-a*r*p+t*l*p)*R,e[8]=y*R,e[9]=(g*u*s-d*x*s-g*n*p+t*x*p+d*n*f-t*u*f)*R,e[10]=(a*x*s-g*o*s+g*n*c-t*x*c-a*n*f+t*o*f)*R,e[11]=(d*o*s-a*u*s-d*n*c+t*u*c+a*n*p-t*o*p)*R,e[12]=C*R,e[13]=(d*x*r-g*u*r+g*n*h-t*x*h-d*n*m+t*u*m)*R,e[14]=(g*o*r-a*x*r-g*n*l+t*x*l+a*n*m-t*o*m)*R,e[15]=(a*u*r-d*o*r+d*n*l-t*u*l-a*n*h+t*o*h)*R,this}scale(e){let t=this.elements,n=e.x,r=e.y,s=e.z;return t[0]*=n,t[4]*=r,t[8]*=s,t[1]*=n,t[5]*=r,t[9]*=s,t[2]*=n,t[6]*=r,t[10]*=s,t[3]*=n,t[7]*=r,t[11]*=s,this}getMaxScaleOnAxis(){let e=this.elements,t=e[0]*e[0]+e[1]*e[1]+e[2]*e[2],n=e[4]*e[4]+e[5]*e[5]+e[6]*e[6],r=e[8]*e[8]+e[9]*e[9]+e[10]*e[10];return Math.sqrt(Math.max(t,n,r))}makeTranslation(e,t,n){return e.isVector3?this.set(1,0,0,e.x,0,1,0,e.y,0,0,1,e.z,0,0,0,1):this.set(1,0,0,e,0,1,0,t,0,0,1,n,0,0,0,1),this}makeRotationX(e){let t=Math.cos(e),n=Math.sin(e);return this.set(1,0,0,0,0,t,-n,0,0,n,t,0,0,0,0,1),this}makeRotationY(e){let t=Math.cos(e),n=Math.sin(e);return this.set(t,0,n,0,0,1,0,0,-n,0,t,0,0,0,0,1),this}makeRotationZ(e){let t=Math.cos(e),n=Math.sin(e);return this.set(t,-n,0,0,n,t,0,0,0,0,1,0,0,0,0,1),this}makeRotationAxis(e,t){let n=Math.cos(t),r=Math.sin(t),s=1-n,a=e.x,o=e.y,l=e.z,c=s*a,d=s*o;return this.set(c*a+n,c*o-r*l,c*l+r*o,0,c*o+r*l,d*o+n,d*l-r*a,0,c*l-r*o,d*l+r*a,s*l*l+n,0,0,0,0,1),this}makeScale(e,t,n){return this.set(e,0,0,0,0,t,0,0,0,0,n,0,0,0,0,1),this}makeShear(e,t,n,r,s,a){return this.set(1,n,s,0,e,1,a,0,t,r,1,0,0,0,0,1),this}compose(e,t,n){let r=this.elements,s=t._x,a=t._y,o=t._z,l=t._w,c=s+s,d=a+a,u=o+o,h=s*c,p=s*d,g=s*u,x=a*d,m=a*u,f=o*u,S=l*c,M=l*d,y=l*u,C=n.x,E=n.y,R=n.z;return r[0]=(1-(x+f))*C,r[1]=(p+y)*C,r[2]=(g-M)*C,r[3]=0,r[4]=(p-y)*E,r[5]=(1-(h+f))*E,r[6]=(m+S)*E,r[7]=0,r[8]=(g+M)*R,r[9]=(m-S)*R,r[10]=(1-(h+x))*R,r[11]=0,r[12]=e.x,r[13]=e.y,r[14]=e.z,r[15]=1,this}decompose(e,t,n){let r=this.elements,s=qi.set(r[0],r[1],r[2]).length(),a=qi.set(r[4],r[5],r[6]).length(),o=qi.set(r[8],r[9],r[10]).length();this.determinant()<0&&(s=-s),e.x=r[12],e.y=r[13],e.z=r[14],gn.copy(this);let c=1/s,d=1/a,u=1/o;return gn.elements[0]*=c,gn.elements[1]*=c,gn.elements[2]*=c,gn.elements[4]*=d,gn.elements[5]*=d,gn.elements[6]*=d,gn.elements[8]*=u,gn.elements[9]*=u,gn.elements[10]*=u,t.setFromRotationMatrix(gn),n.x=s,n.y=a,n.z=o,this}makePerspective(e,t,n,r,s,a,o=yn,l=!1){let c=this.elements,d=2*s/(t-e),u=2*s/(n-r),h=(t+e)/(t-e),p=(n+r)/(n-r),g,x;if(l)g=s/(a-s),x=a*s/(a-s);else if(o===yn)g=-(a+s)/(a-s),x=-2*a*s/(a-s);else if(o===Hr)g=-a/(a-s),x=-a*s/(a-s);else throw new Error("THREE.Matrix4.makePerspective(): Invalid coordinate system: "+o);return c[0]=d,c[4]=0,c[8]=h,c[12]=0,c[1]=0,c[5]=u,c[9]=p,c[13]=0,c[2]=0,c[6]=0,c[10]=g,c[14]=x,c[3]=0,c[7]=0,c[11]=-1,c[15]=0,this}makeOrthographic(e,t,n,r,s,a,o=yn,l=!1){let c=this.elements,d=2/(t-e),u=2/(n-r),h=-(t+e)/(t-e),p=-(n+r)/(n-r),g,x;if(l)g=1/(a-s),x=a/(a-s);else if(o===yn)g=-2/(a-s),x=-(a+s)/(a-s);else if(o===Hr)g=-1/(a-s),x=-s/(a-s);else throw new Error("THREE.Matrix4.makeOrthographic(): Invalid coordinate system: "+o);return c[0]=d,c[4]=0,c[8]=0,c[12]=h,c[1]=0,c[5]=u,c[9]=0,c[13]=p,c[2]=0,c[6]=0,c[10]=g,c[14]=x,c[3]=0,c[7]=0,c[11]=0,c[15]=1,this}equals(e){let t=this.elements,n=e.elements;for(let r=0;r<16;r++)if(t[r]!==n[r])return!1;return!0}fromArray(e,t=0){for(let n=0;n<16;n++)this.elements[n]=e[n+t];return this}toArray(e=[],t=0){let n=this.elements;return e[t]=n[0],e[t+1]=n[1],e[t+2]=n[2],e[t+3]=n[3],e[t+4]=n[4],e[t+5]=n[5],e[t+6]=n[6],e[t+7]=n[7],e[t+8]=n[8],e[t+9]=n[9],e[t+10]=n[10],e[t+11]=n[11],e[t+12]=n[12],e[t+13]=n[13],e[t+14]=n[14],e[t+15]=n[15],e}},qi=new N,gn=new ct,$h=new N(0,0,0),qh=new N(1,1,1),ei=new N,Fs=new N,jt=new N,Gc=new ct,Wc=new Wt,en=class i{constructor(e=0,t=0,n=0,r=i.DEFAULT_ORDER){this.isEuler=!0,this._x=e,this._y=t,this._z=n,this._order=r}get x(){return this._x}set x(e){this._x=e,this._onChangeCallback()}get y(){return this._y}set y(e){this._y=e,this._onChangeCallback()}get z(){return this._z}set z(e){this._z=e,this._onChangeCallback()}get order(){return this._order}set order(e){this._order=e,this._onChangeCallback()}set(e,t,n,r=this._order){return this._x=e,this._y=t,this._z=n,this._order=r,this._onChangeCallback(),this}clone(){return new this.constructor(this._x,this._y,this._z,this._order)}copy(e){return this._x=e._x,this._y=e._y,this._z=e._z,this._order=e._order,this._onChangeCallback(),this}setFromRotationMatrix(e,t=this._order,n=!0){let r=e.elements,s=r[0],a=r[4],o=r[8],l=r[1],c=r[5],d=r[9],u=r[2],h=r[6],p=r[10];switch(t){case"XYZ":this._y=Math.asin(Ge(o,-1,1)),Math.abs(o)<.9999999?(this._x=Math.atan2(-d,p),this._z=Math.atan2(-a,s)):(this._x=Math.atan2(h,c),this._z=0);break;case"YXZ":this._x=Math.asin(-Ge(d,-1,1)),Math.abs(d)<.9999999?(this._y=Math.atan2(o,p),this._z=Math.atan2(l,c)):(this._y=Math.atan2(-u,s),this._z=0);break;case"ZXY":this._x=Math.asin(Ge(h,-1,1)),Math.abs(h)<.9999999?(this._y=Math.atan2(-u,p),this._z=Math.atan2(-a,c)):(this._y=0,this._z=Math.atan2(l,s));break;case"ZYX":this._y=Math.asin(-Ge(u,-1,1)),Math.abs(u)<.9999999?(this._x=Math.atan2(h,p),this._z=Math.atan2(l,s)):(this._x=0,this._z=Math.atan2(-a,c));break;case"YZX":this._z=Math.asin(Ge(l,-1,1)),Math.abs(l)<.9999999?(this._x=Math.atan2(-d,c),this._y=Math.atan2(-u,s)):(this._x=0,this._y=Math.atan2(o,p));break;case"XZY":this._z=Math.asin(-Ge(a,-1,1)),Math.abs(a)<.9999999?(this._x=Math.atan2(h,c),this._y=Math.atan2(o,s)):(this._x=Math.atan2(-d,p),this._y=0);break;default:console.warn("THREE.Euler: .setFromRotationMatrix() encountered an unknown order: "+t)}return this._order=t,n===!0&&this._onChangeCallback(),this}setFromQuaternion(e,t,n){return Gc.makeRotationFromQuaternion(e),this.setFromRotationMatrix(Gc,t,n)}setFromVector3(e,t=this._order){return this.set(e.x,e.y,e.z,t)}reorder(e){return Wc.setFromEuler(this),this.setFromQuaternion(Wc,e)}equals(e){return e._x===this._x&&e._y===this._y&&e._z===this._z&&e._order===this._order}fromArray(e){return this._x=e[0],this._y=e[1],this._z=e[2],e[3]!==void 0&&(this._order=e[3]),this._onChangeCallback(),this}toArray(e=[],t=0){return e[t]=this._x,e[t+1]=this._y,e[t+2]=this._z,e[t+3]=this._order,e}_onChange(e){return this._onChangeCallback=e,this}_onChangeCallback(){}*[Symbol.iterator](){yield this._x,yield this._y,yield this._z,yield this._order}};en.DEFAULT_ORDER="XYZ";var Wr=class{constructor(){this.mask=1}set(e){this.mask=(1<<e|0)>>>0}enable(e){this.mask|=1<<e|0}enableAll(){this.mask=-1}toggle(e){this.mask^=1<<e|0}disable(e){this.mask&=~(1<<e|0)}disableAll(){this.mask=0}test(e){return(this.mask&e.mask)!==0}isEnabled(e){return(this.mask&(1<<e|0))!==0}},Yh=0,Xc=new N,Yi=new Wt,On=new ct,Us=new N,Nr=new N,Zh=new N,Jh=new Wt,$c=new N(1,0,0),qc=new N(0,1,0),Yc=new N(0,0,1),Zc={type:"added"},Kh={type:"removed"},Zi={type:"childadded",child:null},nl={type:"childremoved",child:null},wt=class i extends Gn{constructor(){super(),this.isObject3D=!0,Object.defineProperty(this,"id",{value:Yh++}),this.uuid=kn(),this.name="",this.type="Object3D",this.parent=null,this.children=[],this.up=i.DEFAULT_UP.clone();let e=new N,t=new en,n=new Wt,r=new N(1,1,1);function s(){n.setFromEuler(t,!1)}function a(){t.setFromQuaternion(n,void 0,!1)}t._onChange(s),n._onChange(a),Object.defineProperties(this,{position:{configurable:!0,enumerable:!0,value:e},rotation:{configurable:!0,enumerable:!0,value:t},quaternion:{configurable:!0,enumerable:!0,value:n},scale:{configurable:!0,enumerable:!0,value:r},modelViewMatrix:{value:new ct},normalMatrix:{value:new Oe}}),this.matrix=new ct,this.matrixWorld=new ct,this.matrixAutoUpdate=i.DEFAULT_MATRIX_AUTO_UPDATE,this.matrixWorldAutoUpdate=i.DEFAULT_MATRIX_WORLD_AUTO_UPDATE,this.matrixWorldNeedsUpdate=!1,this.layers=new Wr,this.visible=!0,this.castShadow=!1,this.receiveShadow=!1,this.frustumCulled=!0,this.renderOrder=0,this.animations=[],this.customDepthMaterial=void 0,this.customDistanceMaterial=void 0,this.userData={}}onBeforeShadow(){}onAfterShadow(){}onBeforeRender(){}onAfterRender(){}applyMatrix4(e){this.matrixAutoUpdate&&this.updateMatrix(),this.matrix.premultiply(e),this.matrix.decompose(this.position,this.quaternion,this.scale)}applyQuaternion(e){return this.quaternion.premultiply(e),this}setRotationFromAxisAngle(e,t){this.quaternion.setFromAxisAngle(e,t)}setRotationFromEuler(e){this.quaternion.setFromEuler(e,!0)}setRotationFromMatrix(e){this.quaternion.setFromRotationMatrix(e)}setRotationFromQuaternion(e){this.quaternion.copy(e)}rotateOnAxis(e,t){return Yi.setFromAxisAngle(e,t),this.quaternion.multiply(Yi),this}rotateOnWorldAxis(e,t){return Yi.setFromAxisAngle(e,t),this.quaternion.premultiply(Yi),this}rotateX(e){return this.rotateOnAxis($c,e)}rotateY(e){return this.rotateOnAxis(qc,e)}rotateZ(e){return this.rotateOnAxis(Yc,e)}translateOnAxis(e,t){return Xc.copy(e).applyQuaternion(this.quaternion),this.position.add(Xc.multiplyScalar(t)),this}translateX(e){return this.translateOnAxis($c,e)}translateY(e){return this.translateOnAxis(qc,e)}translateZ(e){return this.translateOnAxis(Yc,e)}localToWorld(e){return this.updateWorldMatrix(!0,!1),e.applyMatrix4(this.matrixWorld)}worldToLocal(e){return this.updateWorldMatrix(!0,!1),e.applyMatrix4(On.copy(this.matrixWorld).invert())}lookAt(e,t,n){e.isVector3?Us.copy(e):Us.set(e,t,n);let r=this.parent;this.updateWorldMatrix(!0,!1),Nr.setFromMatrixPosition(this.matrixWorld),this.isCamera||this.isLight?On.lookAt(Nr,Us,this.up):On.lookAt(Us,Nr,this.up),this.quaternion.setFromRotationMatrix(On),r&&(On.extractRotation(r.matrixWorld),Yi.setFromRotationMatrix(On),this.quaternion.premultiply(Yi.invert()))}add(e){if(arguments.length>1){for(let t=0;t<arguments.length;t++)this.add(arguments[t]);return this}return e===this?(console.error("THREE.Object3D.add: object can't be added as a child of itself.",e),this):(e&&e.isObject3D?(e.removeFromParent(),e.parent=this,this.children.push(e),e.dispatchEvent(Zc),Zi.child=e,this.dispatchEvent(Zi),Zi.child=null):console.error("THREE.Object3D.add: object not an instance of THREE.Object3D.",e),this)}remove(e){if(arguments.length>1){for(let n=0;n<arguments.length;n++)this.remove(arguments[n]);return this}let t=this.children.indexOf(e);return t!==-1&&(e.parent=null,this.children.splice(t,1),e.dispatchEvent(Kh),nl.child=e,this.dispatchEvent(nl),nl.child=null),this}removeFromParent(){let e=this.parent;return e!==null&&e.remove(this),this}clear(){return this.remove(...this.children)}attach(e){return this.updateWorldMatrix(!0,!1),On.copy(this.matrixWorld).invert(),e.parent!==null&&(e.parent.updateWorldMatrix(!0,!1),On.multiply(e.parent.matrixWorld)),e.applyMatrix4(On),e.removeFromParent(),e.parent=this,this.children.push(e),e.updateWorldMatrix(!1,!0),e.dispatchEvent(Zc),Zi.child=e,this.dispatchEvent(Zi),Zi.child=null,this}getObjectById(e){return this.getObjectByProperty("id",e)}getObjectByName(e){return this.getObjectByProperty("name",e)}getObjectByProperty(e,t){if(this[e]===t)return this;for(let n=0,r=this.children.length;n<r;n++){let a=this.children[n].getObjectByProperty(e,t);if(a!==void 0)return a}}getObjectsByProperty(e,t,n=[]){this[e]===t&&n.push(this);let r=this.children;for(let s=0,a=r.length;s<a;s++)r[s].getObjectsByProperty(e,t,n);return n}getWorldPosition(e){return this.updateWorldMatrix(!0,!1),e.setFromMatrixPosition(this.matrixWorld)}getWorldQuaternion(e){return this.updateWorldMatrix(!0,!1),this.matrixWorld.decompose(Nr,e,Zh),e}getWorldScale(e){return this.updateWorldMatrix(!0,!1),this.matrixWorld.decompose(Nr,Jh,e),e}getWorldDirection(e){this.updateWorldMatrix(!0,!1);let t=this.matrixWorld.elements;return e.set(t[8],t[9],t[10]).normalize()}raycast(){}traverse(e){e(this);let t=this.children;for(let n=0,r=t.length;n<r;n++)t[n].traverse(e)}traverseVisible(e){if(this.visible===!1)return;e(this);let t=this.children;for(let n=0,r=t.length;n<r;n++)t[n].traverseVisible(e)}traverseAncestors(e){let t=this.parent;t!==null&&(e(t),t.traverseAncestors(e))}updateMatrix(){this.matrix.compose(this.position,this.quaternion,this.scale),this.matrixWorldNeedsUpdate=!0}updateMatrixWorld(e){this.matrixAutoUpdate&&this.updateMatrix(),(this.matrixWorldNeedsUpdate||e)&&(this.matrixWorldAutoUpdate===!0&&(this.parent===null?this.matrixWorld.copy(this.matrix):this.matrixWorld.multiplyMatrices(this.parent.matrixWorld,this.matrix)),this.matrixWorldNeedsUpdate=!1,e=!0);let t=this.children;for(let n=0,r=t.length;n<r;n++)t[n].updateMatrixWorld(e)}updateWorldMatrix(e,t){let n=this.parent;if(e===!0&&n!==null&&n.updateWorldMatrix(!0,!1),this.matrixAutoUpdate&&this.updateMatrix(),this.matrixWorldAutoUpdate===!0&&(this.parent===null?this.matrixWorld.copy(this.matrix):this.matrixWorld.multiplyMatrices(this.parent.matrixWorld,this.matrix)),t===!0){let r=this.children;for(let s=0,a=r.length;s<a;s++)r[s].updateWorldMatrix(!1,!0)}}toJSON(e){let t=e===void 0||typeof e=="string",n={};t&&(e={geometries:{},materials:{},textures:{},images:{},shapes:{},skeletons:{},animations:{},nodes:{}},n.metadata={version:4.7,type:"Object",generator:"Object3D.toJSON"});let r={};r.uuid=this.uuid,r.type=this.type,this.name!==""&&(r.name=this.name),this.castShadow===!0&&(r.castShadow=!0),this.receiveShadow===!0&&(r.receiveShadow=!0),this.visible===!1&&(r.visible=!1),this.frustumCulled===!1&&(r.frustumCulled=!1),this.renderOrder!==0&&(r.renderOrder=this.renderOrder),Object.keys(this.userData).length>0&&(r.userData=this.userData),r.layers=this.layers.mask,r.matrix=this.matrix.toArray(),r.up=this.up.toArray(),this.matrixAutoUpdate===!1&&(r.matrixAutoUpdate=!1),this.isInstancedMesh&&(r.type="InstancedMesh",r.count=this.count,r.instanceMatrix=this.instanceMatrix.toJSON(),this.instanceColor!==null&&(r.instanceColor=this.instanceColor.toJSON())),this.isBatchedMesh&&(r.type="BatchedMesh",r.perObjectFrustumCulled=this.perObjectFrustumCulled,r.sortObjects=this.sortObjects,r.drawRanges=this._drawRanges,r.reservedRanges=this._reservedRanges,r.geometryInfo=this._geometryInfo.map(o=>({...o,boundingBox:o.boundingBox?o.boundingBox.toJSON():void 0,boundingSphere:o.boundingSphere?o.boundingSphere.toJSON():void 0})),r.instanceInfo=this._instanceInfo.map(o=>({...o})),r.availableInstanceIds=this._availableInstanceIds.slice(),r.availableGeometryIds=this._availableGeometryIds.slice(),r.nextIndexStart=this._nextIndexStart,r.nextVertexStart=this._nextVertexStart,r.geometryCount=this._geometryCount,r.maxInstanceCount=this._maxInstanceCount,r.maxVertexCount=this._maxVertexCount,r.maxIndexCount=this._maxIndexCount,r.geometryInitialized=this._geometryInitialized,r.matricesTexture=this._matricesTexture.toJSON(e),r.indirectTexture=this._indirectTexture.toJSON(e),this._colorsTexture!==null&&(r.colorsTexture=this._colorsTexture.toJSON(e)),this.boundingSphere!==null&&(r.boundingSphere=this.boundingSphere.toJSON()),this.boundingBox!==null&&(r.boundingBox=this.boundingBox.toJSON()));function s(o,l){return o[l.uuid]===void 0&&(o[l.uuid]=l.toJSON(e)),l.uuid}if(this.isScene)this.background&&(this.background.isColor?r.background=this.background.toJSON():this.background.isTexture&&(r.background=this.background.toJSON(e).uuid)),this.environment&&this.environment.isTexture&&this.environment.isRenderTargetTexture!==!0&&(r.environment=this.environment.toJSON(e).uuid);else if(this.isMesh||this.isLine||this.isPoints){r.geometry=s(e.geometries,this.geometry);let o=this.geometry.parameters;if(o!==void 0&&o.shapes!==void 0){let l=o.shapes;if(Array.isArray(l))for(let c=0,d=l.length;c<d;c++){let u=l[c];s(e.shapes,u)}else s(e.shapes,l)}}if(this.isSkinnedMesh&&(r.bindMode=this.bindMode,r.bindMatrix=this.bindMatrix.toArray(),this.skeleton!==void 0&&(s(e.skeletons,this.skeleton),r.skeleton=this.skeleton.uuid)),this.material!==void 0)if(Array.isArray(this.material)){let o=[];for(let l=0,c=this.material.length;l<c;l++)o.push(s(e.materials,this.material[l]));r.material=o}else r.material=s(e.materials,this.material);if(this.children.length>0){r.children=[];for(let o=0;o<this.children.length;o++)r.children.push(this.children[o].toJSON(e).object)}if(this.animations.length>0){r.animations=[];for(let o=0;o<this.animations.length;o++){let l=this.animations[o];r.animations.push(s(e.animations,l))}}if(t){let o=a(e.geometries),l=a(e.materials),c=a(e.textures),d=a(e.images),u=a(e.shapes),h=a(e.skeletons),p=a(e.animations),g=a(e.nodes);o.length>0&&(n.geometries=o),l.length>0&&(n.materials=l),c.length>0&&(n.textures=c),d.length>0&&(n.images=d),u.length>0&&(n.shapes=u),h.length>0&&(n.skeletons=h),p.length>0&&(n.animations=p),g.length>0&&(n.nodes=g)}return n.object=r,n;function a(o){let l=[];for(let c in o){let d=o[c];delete d.metadata,l.push(d)}return l}}clone(e){return new this.constructor().copy(this,e)}copy(e,t=!0){if(this.name=e.name,this.up.copy(e.up),this.position.copy(e.position),this.rotation.order=e.rotation.order,this.quaternion.copy(e.quaternion),this.scale.copy(e.scale),this.matrix.copy(e.matrix),this.matrixWorld.copy(e.matrixWorld),this.matrixAutoUpdate=e.matrixAutoUpdate,this.matrixWorldAutoUpdate=e.matrixWorldAutoUpdate,this.matrixWorldNeedsUpdate=e.matrixWorldNeedsUpdate,this.layers.mask=e.layers.mask,this.visible=e.visible,this.castShadow=e.castShadow,this.receiveShadow=e.receiveShadow,this.frustumCulled=e.frustumCulled,this.renderOrder=e.renderOrder,this.animations=e.animations.slice(),this.userData=JSON.parse(JSON.stringify(e.userData)),t===!0)for(let n=0;n<e.children.length;n++){let r=e.children[n];this.add(r.clone())}return this}};wt.DEFAULT_UP=new N(0,1,0);wt.DEFAULT_MATRIX_AUTO_UPDATE=!0;wt.DEFAULT_MATRIX_WORLD_AUTO_UPDATE=!0;var xn=new N,Bn=new N,il=new N,zn=new N,Ji=new N,Ki=new N,Jc=new N,rl=new N,sl=new N,al=new N,ol=new pt,ll=new pt,cl=new pt,An=class i{constructor(e=new N,t=new N,n=new N){this.a=e,this.b=t,this.c=n}static getNormal(e,t,n,r){r.subVectors(n,t),xn.subVectors(e,t),r.cross(xn);let s=r.lengthSq();return s>0?r.multiplyScalar(1/Math.sqrt(s)):r.set(0,0,0)}static getBarycoord(e,t,n,r,s){xn.subVectors(r,t),Bn.subVectors(n,t),il.subVectors(e,t);let a=xn.dot(xn),o=xn.dot(Bn),l=xn.dot(il),c=Bn.dot(Bn),d=Bn.dot(il),u=a*c-o*o;if(u===0)return s.set(0,0,0),null;let h=1/u,p=(c*l-o*d)*h,g=(a*d-o*l)*h;return s.set(1-p-g,g,p)}static containsPoint(e,t,n,r){return this.getBarycoord(e,t,n,r,zn)===null?!1:zn.x>=0&&zn.y>=0&&zn.x+zn.y<=1}static getInterpolation(e,t,n,r,s,a,o,l){return this.getBarycoord(e,t,n,r,zn)===null?(l.x=0,l.y=0,"z"in l&&(l.z=0),"w"in l&&(l.w=0),null):(l.setScalar(0),l.addScaledVector(s,zn.x),l.addScaledVector(a,zn.y),l.addScaledVector(o,zn.z),l)}static getInterpolatedAttribute(e,t,n,r,s,a){return ol.setScalar(0),ll.setScalar(0),cl.setScalar(0),ol.fromBufferAttribute(e,t),ll.fromBufferAttribute(e,n),cl.fromBufferAttribute(e,r),a.setScalar(0),a.addScaledVector(ol,s.x),a.addScaledVector(ll,s.y),a.addScaledVector(cl,s.z),a}static isFrontFacing(e,t,n,r){return xn.subVectors(n,t),Bn.subVectors(e,t),xn.cross(Bn).dot(r)<0}set(e,t,n){return this.a.copy(e),this.b.copy(t),this.c.copy(n),this}setFromPointsAndIndices(e,t,n,r){return this.a.copy(e[t]),this.b.copy(e[n]),this.c.copy(e[r]),this}setFromAttributeAndIndices(e,t,n,r){return this.a.fromBufferAttribute(e,t),this.b.fromBufferAttribute(e,n),this.c.fromBufferAttribute(e,r),this}clone(){return new this.constructor().copy(this)}copy(e){return this.a.copy(e.a),this.b.copy(e.b),this.c.copy(e.c),this}getArea(){return xn.subVectors(this.c,this.b),Bn.subVectors(this.a,this.b),xn.cross(Bn).length()*.5}getMidpoint(e){return e.addVectors(this.a,this.b).add(this.c).multiplyScalar(1/3)}getNormal(e){return i.getNormal(this.a,this.b,this.c,e)}getPlane(e){return e.setFromCoplanarPoints(this.a,this.b,this.c)}getBarycoord(e,t){return i.getBarycoord(e,this.a,this.b,this.c,t)}getInterpolation(e,t,n,r,s){return i.getInterpolation(e,this.a,this.b,this.c,t,n,r,s)}containsPoint(e){return i.containsPoint(e,this.a,this.b,this.c)}isFrontFacing(e){return i.isFrontFacing(this.a,this.b,this.c,e)}intersectsBox(e){return e.intersectsTriangle(this)}closestPointToPoint(e,t){let n=this.a,r=this.b,s=this.c,a,o;Ji.subVectors(r,n),Ki.subVectors(s,n),rl.subVectors(e,n);let l=Ji.dot(rl),c=Ki.dot(rl);if(l<=0&&c<=0)return t.copy(n);sl.subVectors(e,r);let d=Ji.dot(sl),u=Ki.dot(sl);if(d>=0&&u<=d)return t.copy(r);let h=l*u-d*c;if(h<=0&&l>=0&&d<=0)return a=l/(l-d),t.copy(n).addScaledVector(Ji,a);al.subVectors(e,s);let p=Ji.dot(al),g=Ki.dot(al);if(g>=0&&p<=g)return t.copy(s);let x=p*c-l*g;if(x<=0&&c>=0&&g<=0)return o=c/(c-g),t.copy(n).addScaledVector(Ki,o);let m=d*g-p*u;if(m<=0&&u-d>=0&&p-g>=0)return Jc.subVectors(s,r),o=(u-d)/(u-d+(p-g)),t.copy(r).addScaledVector(Jc,o);let f=1/(m+x+h);return a=x*f,o=h*f,t.copy(n).addScaledVector(Ji,a).addScaledVector(Ki,o)}equals(e){return e.a.equals(this.a)&&e.b.equals(this.b)&&e.c.equals(this.c)}},nu={aliceblue:15792383,antiquewhite:16444375,aqua:65535,aquamarine:8388564,azure:15794175,beige:16119260,bisque:16770244,black:0,blanchedalmond:16772045,blue:255,blueviolet:9055202,brown:10824234,burlywood:14596231,cadetblue:6266528,chartreuse:8388352,chocolate:13789470,coral:16744272,cornflowerblue:6591981,cornsilk:16775388,crimson:14423100,cyan:65535,darkblue:139,darkcyan:35723,darkgoldenrod:12092939,darkgray:11119017,darkgreen:25600,darkgrey:11119017,darkkhaki:12433259,darkmagenta:9109643,darkolivegreen:5597999,darkorange:16747520,darkorchid:10040012,darkred:9109504,darksalmon:15308410,darkseagreen:9419919,darkslateblue:4734347,darkslategray:3100495,darkslategrey:3100495,darkturquoise:52945,darkviolet:9699539,deeppink:16716947,deepskyblue:49151,dimgray:6908265,dimgrey:6908265,dodgerblue:2003199,firebrick:11674146,floralwhite:16775920,forestgreen:2263842,fuchsia:16711935,gainsboro:14474460,ghostwhite:16316671,gold:16766720,goldenrod:14329120,gray:8421504,green:32768,greenyellow:11403055,grey:8421504,honeydew:15794160,hotpink:16738740,indianred:13458524,indigo:4915330,ivory:16777200,khaki:15787660,lavender:15132410,lavenderblush:16773365,lawngreen:8190976,lemonchiffon:16775885,lightblue:11393254,lightcoral:15761536,lightcyan:14745599,lightgoldenrodyellow:16448210,lightgray:13882323,lightgreen:9498256,lightgrey:13882323,lightpink:16758465,lightsalmon:16752762,lightseagreen:2142890,lightskyblue:8900346,lightslategray:7833753,lightslategrey:7833753,lightsteelblue:11584734,lightyellow:16777184,lime:65280,limegreen:3329330,linen:16445670,magenta:16711935,maroon:8388608,mediumaquamarine:6737322,mediumblue:205,mediumorchid:12211667,mediumpurple:9662683,mediumseagreen:3978097,mediumslateblue:8087790,mediumspringgreen:64154,mediumturquoise:4772300,mediumvioletred:13047173,midnightblue:1644912,mintcream:16121850,mistyrose:16770273,moccasin:16770229,navajowhite:16768685,navy:128,oldlace:16643558,olive:8421376,olivedrab:7048739,orange:16753920,orangered:16729344,orchid:14315734,palegoldenrod:15657130,palegreen:10025880,paleturquoise:11529966,palevioletred:14381203,papayawhip:16773077,peachpuff:16767673,peru:13468991,pink:16761035,plum:14524637,powderblue:11591910,purple:8388736,rebeccapurple:6697881,red:16711680,rosybrown:12357519,royalblue:4286945,saddlebrown:9127187,salmon:16416882,sandybrown:16032864,seagreen:3050327,seashell:16774638,sienna:10506797,silver:12632256,skyblue:8900331,slateblue:6970061,slategray:7372944,slategrey:7372944,snow:16775930,springgreen:65407,steelblue:4620980,tan:13808780,teal:32896,thistle:14204888,tomato:16737095,turquoise:4251856,violet:15631086,wheat:16113331,white:16777215,whitesmoke:16119285,yellow:16776960,yellowgreen:10145074},ti={h:0,s:0,l:0},Os={h:0,s:0,l:0};function dl(i,e,t){return t<0&&(t+=1),t>1&&(t-=1),t<1/6?i+(e-i)*6*t:t<1/2?e:t<2/3?i+(e-i)*6*(2/3-t):i}var Ne=class{constructor(e,t,n){return this.isColor=!0,this.r=1,this.g=1,this.b=1,this.set(e,t,n)}set(e,t,n){if(t===void 0&&n===void 0){let r=e;r&&r.isColor?this.copy(r):typeof r=="number"?this.setHex(r):typeof r=="string"&&this.setStyle(r)}else this.setRGB(e,t,n);return this}setScalar(e){return this.r=e,this.g=e,this.b=e,this}setHex(e,t=Nt){return e=Math.floor(e),this.r=(e>>16&255)/255,this.g=(e>>8&255)/255,this.b=(e&255)/255,$e.colorSpaceToWorking(this,t),this}setRGB(e,t,n,r=$e.workingColorSpace){return this.r=e,this.g=t,this.b=n,$e.colorSpaceToWorking(this,r),this}setHSL(e,t,n,r=$e.workingColorSpace){if(e=Xl(e,1),t=Ge(t,0,1),n=Ge(n,0,1),t===0)this.r=this.g=this.b=n;else{let s=n<=.5?n*(1+t):n+t-n*t,a=2*n-s;this.r=dl(a,s,e+1/3),this.g=dl(a,s,e),this.b=dl(a,s,e-1/3)}return $e.colorSpaceToWorking(this,r),this}setStyle(e,t=Nt){function n(s){s!==void 0&&parseFloat(s)<1&&console.warn("THREE.Color: Alpha component of "+e+" will be ignored.")}let r;if(r=/^(\w+)\(([^\)]*)\)/.exec(e)){let s,a=r[1],o=r[2];switch(a){case"rgb":case"rgba":if(s=/^\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*(?:,\s*(\d*\.?\d+)\s*)?$/.exec(o))return n(s[4]),this.setRGB(Math.min(255,parseInt(s[1],10))/255,Math.min(255,parseInt(s[2],10))/255,Math.min(255,parseInt(s[3],10))/255,t);if(s=/^\s*(\d+)\%\s*,\s*(\d+)\%\s*,\s*(\d+)\%\s*(?:,\s*(\d*\.?\d+)\s*)?$/.exec(o))return n(s[4]),this.setRGB(Math.min(100,parseInt(s[1],10))/100,Math.min(100,parseInt(s[2],10))/100,Math.min(100,parseInt(s[3],10))/100,t);break;case"hsl":case"hsla":if(s=/^\s*(\d*\.?\d+)\s*,\s*(\d*\.?\d+)\%\s*,\s*(\d*\.?\d+)\%\s*(?:,\s*(\d*\.?\d+)\s*)?$/.exec(o))return n(s[4]),this.setHSL(parseFloat(s[1])/360,parseFloat(s[2])/100,parseFloat(s[3])/100,t);break;default:console.warn("THREE.Color: Unknown color model "+e)}}else if(r=/^\#([A-Fa-f\d]+)$/.exec(e)){let s=r[1],a=s.length;if(a===3)return this.setRGB(parseInt(s.charAt(0),16)/15,parseInt(s.charAt(1),16)/15,parseInt(s.charAt(2),16)/15,t);if(a===6)return this.setHex(parseInt(s,16),t);console.warn("THREE.Color: Invalid hex color "+e)}else if(e&&e.length>0)return this.setColorName(e,t);return this}setColorName(e,t=Nt){let n=nu[e.toLowerCase()];return n!==void 0?this.setHex(n,t):console.warn("THREE.Color: Unknown color "+e),this}clone(){return new this.constructor(this.r,this.g,this.b)}copy(e){return this.r=e.r,this.g=e.g,this.b=e.b,this}copySRGBToLinear(e){return this.r=Hn(e.r),this.g=Hn(e.g),this.b=Hn(e.b),this}copyLinearToSRGB(e){return this.r=ar(e.r),this.g=ar(e.g),this.b=ar(e.b),this}convertSRGBToLinear(){return this.copySRGBToLinear(this),this}convertLinearToSRGB(){return this.copyLinearToSRGB(this),this}getHex(e=Nt){return $e.workingToColorSpace(Pt.copy(this),e),Math.round(Ge(Pt.r*255,0,255))*65536+Math.round(Ge(Pt.g*255,0,255))*256+Math.round(Ge(Pt.b*255,0,255))}getHexString(e=Nt){return("000000"+this.getHex(e).toString(16)).slice(-6)}getHSL(e,t=$e.workingColorSpace){$e.workingToColorSpace(Pt.copy(this),t);let n=Pt.r,r=Pt.g,s=Pt.b,a=Math.max(n,r,s),o=Math.min(n,r,s),l,c,d=(o+a)/2;if(o===a)l=0,c=0;else{let u=a-o;switch(c=d<=.5?u/(a+o):u/(2-a-o),a){case n:l=(r-s)/u+(r<s?6:0);break;case r:l=(s-n)/u+2;break;case s:l=(n-r)/u+4;break}l/=6}return e.h=l,e.s=c,e.l=d,e}getRGB(e,t=$e.workingColorSpace){return $e.workingToColorSpace(Pt.copy(this),t),e.r=Pt.r,e.g=Pt.g,e.b=Pt.b,e}getStyle(e=Nt){$e.workingToColorSpace(Pt.copy(this),e);let t=Pt.r,n=Pt.g,r=Pt.b;return e!==Nt?`color(${e} ${t.toFixed(3)} ${n.toFixed(3)} ${r.toFixed(3)})`:`rgb(${Math.round(t*255)},${Math.round(n*255)},${Math.round(r*255)})`}offsetHSL(e,t,n){return this.getHSL(ti),this.setHSL(ti.h+e,ti.s+t,ti.l+n)}add(e){return this.r+=e.r,this.g+=e.g,this.b+=e.b,this}addColors(e,t){return this.r=e.r+t.r,this.g=e.g+t.g,this.b=e.b+t.b,this}addScalar(e){return this.r+=e,this.g+=e,this.b+=e,this}sub(e){return this.r=Math.max(0,this.r-e.r),this.g=Math.max(0,this.g-e.g),this.b=Math.max(0,this.b-e.b),this}multiply(e){return this.r*=e.r,this.g*=e.g,this.b*=e.b,this}multiplyScalar(e){return this.r*=e,this.g*=e,this.b*=e,this}lerp(e,t){return this.r+=(e.r-this.r)*t,this.g+=(e.g-this.g)*t,this.b+=(e.b-this.b)*t,this}lerpColors(e,t,n){return this.r=e.r+(t.r-e.r)*n,this.g=e.g+(t.g-e.g)*n,this.b=e.b+(t.b-e.b)*n,this}lerpHSL(e,t){this.getHSL(ti),e.getHSL(Os);let n=Br(ti.h,Os.h,t),r=Br(ti.s,Os.s,t),s=Br(ti.l,Os.l,t);return this.setHSL(n,r,s),this}setFromVector3(e){return this.r=e.x,this.g=e.y,this.b=e.z,this}applyMatrix3(e){let t=this.r,n=this.g,r=this.b,s=e.elements;return this.r=s[0]*t+s[3]*n+s[6]*r,this.g=s[1]*t+s[4]*n+s[7]*r,this.b=s[2]*t+s[5]*n+s[8]*r,this}equals(e){return e.r===this.r&&e.g===this.g&&e.b===this.b}fromArray(e,t=0){return this.r=e[t],this.g=e[t+1],this.b=e[t+2],this}toArray(e=[],t=0){return e[t]=this.r,e[t+1]=this.g,e[t+2]=this.b,e}fromBufferAttribute(e,t){return this.r=e.getX(t),this.g=e.getY(t),this.b=e.getZ(t),this}toJSON(){return this.getHex()}*[Symbol.iterator](){yield this.r,yield this.g,yield this.b}},Pt=new Ne;Ne.NAMES=nu;var jh=0,bn=class extends Gn{constructor(){super(),this.isMaterial=!0,Object.defineProperty(this,"id",{value:jh++}),this.uuid=kn(),this.name="",this.type="Material",this.blending=wi,this.side=Vn,this.vertexColors=!1,this.opacity=1,this.transparent=!1,this.alphaHash=!1,this.blendSrc=aa,this.blendDst=oa,this.blendEquation=ri,this.blendSrcAlpha=null,this.blendDstAlpha=null,this.blendEquationAlpha=null,this.blendColor=new Ne(0,0,0),this.blendAlpha=0,this.depthFunc=Mi,this.depthTest=!0,this.depthWrite=!0,this.stencilWriteMask=255,this.stencilFunc=wl,this.stencilRef=0,this.stencilFuncMask=255,this.stencilFail=bi,this.stencilZFail=bi,this.stencilZPass=bi,this.stencilWrite=!1,this.clippingPlanes=null,this.clipIntersection=!1,this.clipShadows=!1,this.shadowSide=null,this.colorWrite=!0,this.precision=null,this.polygonOffset=!1,this.polygonOffsetFactor=0,this.polygonOffsetUnits=0,this.dithering=!1,this.alphaToCoverage=!1,this.premultipliedAlpha=!1,this.forceSinglePass=!1,this.allowOverride=!0,this.visible=!0,this.toneMapped=!0,this.userData={},this.version=0,this._alphaTest=0}get alphaTest(){return this._alphaTest}set alphaTest(e){this._alphaTest>0!=e>0&&this.version++,this._alphaTest=e}onBeforeRender(){}onBeforeCompile(){}customProgramCacheKey(){return this.onBeforeCompile.toString()}setValues(e){if(e!==void 0)for(let t in e){let n=e[t];if(n===void 0){console.warn(`THREE.Material: parameter '${t}' has value of undefined.`);continue}let r=this[t];if(r===void 0){console.warn(`THREE.Material: '${t}' is not a property of THREE.${this.type}.`);continue}r&&r.isColor?r.set(n):r&&r.isVector3&&n&&n.isVector3?r.copy(n):this[t]=n}}toJSON(e){let t=e===void 0||typeof e=="string";t&&(e={textures:{},images:{}});let n={metadata:{version:4.7,type:"Material",generator:"Material.toJSON"}};n.uuid=this.uuid,n.type=this.type,this.name!==""&&(n.name=this.name),this.color&&this.color.isColor&&(n.color=this.color.getHex()),this.roughness!==void 0&&(n.roughness=this.roughness),this.metalness!==void 0&&(n.metalness=this.metalness),this.sheen!==void 0&&(n.sheen=this.sheen),this.sheenColor&&this.sheenColor.isColor&&(n.sheenColor=this.sheenColor.getHex()),this.sheenRoughness!==void 0&&(n.sheenRoughness=this.sheenRoughness),this.emissive&&this.emissive.isColor&&(n.emissive=this.emissive.getHex()),this.emissiveIntensity!==void 0&&this.emissiveIntensity!==1&&(n.emissiveIntensity=this.emissiveIntensity),this.specular&&this.specular.isColor&&(n.specular=this.specular.getHex()),this.specularIntensity!==void 0&&(n.specularIntensity=this.specularIntensity),this.specularColor&&this.specularColor.isColor&&(n.specularColor=this.specularColor.getHex()),this.shininess!==void 0&&(n.shininess=this.shininess),this.clearcoat!==void 0&&(n.clearcoat=this.clearcoat),this.clearcoatRoughness!==void 0&&(n.clearcoatRoughness=this.clearcoatRoughness),this.clearcoatMap&&this.clearcoatMap.isTexture&&(n.clearcoatMap=this.clearcoatMap.toJSON(e).uuid),this.clearcoatRoughnessMap&&this.clearcoatRoughnessMap.isTexture&&(n.clearcoatRoughnessMap=this.clearcoatRoughnessMap.toJSON(e).uuid),this.clearcoatNormalMap&&this.clearcoatNormalMap.isTexture&&(n.clearcoatNormalMap=this.clearcoatNormalMap.toJSON(e).uuid,n.clearcoatNormalScale=this.clearcoatNormalScale.toArray()),this.sheenColorMap&&this.sheenColorMap.isTexture&&(n.sheenColorMap=this.sheenColorMap.toJSON(e).uuid),this.sheenRoughnessMap&&this.sheenRoughnessMap.isTexture&&(n.sheenRoughnessMap=this.sheenRoughnessMap.toJSON(e).uuid),this.dispersion!==void 0&&(n.dispersion=this.dispersion),this.iridescence!==void 0&&(n.iridescence=this.iridescence),this.iridescenceIOR!==void 0&&(n.iridescenceIOR=this.iridescenceIOR),this.iridescenceThicknessRange!==void 0&&(n.iridescenceThicknessRange=this.iridescenceThicknessRange),this.iridescenceMap&&this.iridescenceMap.isTexture&&(n.iridescenceMap=this.iridescenceMap.toJSON(e).uuid),this.iridescenceThicknessMap&&this.iridescenceThicknessMap.isTexture&&(n.iridescenceThicknessMap=this.iridescenceThicknessMap.toJSON(e).uuid),this.anisotropy!==void 0&&(n.anisotropy=this.anisotropy),this.anisotropyRotation!==void 0&&(n.anisotropyRotation=this.anisotropyRotation),this.anisotropyMap&&this.anisotropyMap.isTexture&&(n.anisotropyMap=this.anisotropyMap.toJSON(e).uuid),this.map&&this.map.isTexture&&(n.map=this.map.toJSON(e).uuid),this.matcap&&this.matcap.isTexture&&(n.matcap=this.matcap.toJSON(e).uuid),this.alphaMap&&this.alphaMap.isTexture&&(n.alphaMap=this.alphaMap.toJSON(e).uuid),this.lightMap&&this.lightMap.isTexture&&(n.lightMap=this.lightMap.toJSON(e).uuid,n.lightMapIntensity=this.lightMapIntensity),this.aoMap&&this.aoMap.isTexture&&(n.aoMap=this.aoMap.toJSON(e).uuid,n.aoMapIntensity=this.aoMapIntensity),this.bumpMap&&this.bumpMap.isTexture&&(n.bumpMap=this.bumpMap.toJSON(e).uuid,n.bumpScale=this.bumpScale),this.normalMap&&this.normalMap.isTexture&&(n.normalMap=this.normalMap.toJSON(e).uuid,n.normalMapType=this.normalMapType,n.normalScale=this.normalScale.toArray()),this.displacementMap&&this.displacementMap.isTexture&&(n.displacementMap=this.displacementMap.toJSON(e).uuid,n.displacementScale=this.displacementScale,n.displacementBias=this.displacementBias),this.roughnessMap&&this.roughnessMap.isTexture&&(n.roughnessMap=this.roughnessMap.toJSON(e).uuid),this.metalnessMap&&this.metalnessMap.isTexture&&(n.metalnessMap=this.metalnessMap.toJSON(e).uuid),this.emissiveMap&&this.emissiveMap.isTexture&&(n.emissiveMap=this.emissiveMap.toJSON(e).uuid),this.specularMap&&this.specularMap.isTexture&&(n.specularMap=this.specularMap.toJSON(e).uuid),this.specularIntensityMap&&this.specularIntensityMap.isTexture&&(n.specularIntensityMap=this.specularIntensityMap.toJSON(e).uuid),this.specularColorMap&&this.specularColorMap.isTexture&&(n.specularColorMap=this.specularColorMap.toJSON(e).uuid),this.envMap&&this.envMap.isTexture&&(n.envMap=this.envMap.toJSON(e).uuid,this.combine!==void 0&&(n.combine=this.combine)),this.envMapRotation!==void 0&&(n.envMapRotation=this.envMapRotation.toArray()),this.envMapIntensity!==void 0&&(n.envMapIntensity=this.envMapIntensity),this.reflectivity!==void 0&&(n.reflectivity=this.reflectivity),this.refractionRatio!==void 0&&(n.refractionRatio=this.refractionRatio),this.gradientMap&&this.gradientMap.isTexture&&(n.gradientMap=this.gradientMap.toJSON(e).uuid),this.transmission!==void 0&&(n.transmission=this.transmission),this.transmissionMap&&this.transmissionMap.isTexture&&(n.transmissionMap=this.transmissionMap.toJSON(e).uuid),this.thickness!==void 0&&(n.thickness=this.thickness),this.thicknessMap&&this.thicknessMap.isTexture&&(n.thicknessMap=this.thicknessMap.toJSON(e).uuid),this.attenuationDistance!==void 0&&this.attenuationDistance!==1/0&&(n.attenuationDistance=this.attenuationDistance),this.attenuationColor!==void 0&&(n.attenuationColor=this.attenuationColor.getHex()),this.size!==void 0&&(n.size=this.size),this.shadowSide!==null&&(n.shadowSide=this.shadowSide),this.sizeAttenuation!==void 0&&(n.sizeAttenuation=this.sizeAttenuation),this.blending!==wi&&(n.blending=this.blending),this.side!==Vn&&(n.side=this.side),this.vertexColors===!0&&(n.vertexColors=!0),this.opacity<1&&(n.opacity=this.opacity),this.transparent===!0&&(n.transparent=!0),this.blendSrc!==aa&&(n.blendSrc=this.blendSrc),this.blendDst!==oa&&(n.blendDst=this.blendDst),this.blendEquation!==ri&&(n.blendEquation=this.blendEquation),this.blendSrcAlpha!==null&&(n.blendSrcAlpha=this.blendSrcAlpha),this.blendDstAlpha!==null&&(n.blendDstAlpha=this.blendDstAlpha),this.blendEquationAlpha!==null&&(n.blendEquationAlpha=this.blendEquationAlpha),this.blendColor&&this.blendColor.isColor&&(n.blendColor=this.blendColor.getHex()),this.blendAlpha!==0&&(n.blendAlpha=this.blendAlpha),this.depthFunc!==Mi&&(n.depthFunc=this.depthFunc),this.depthTest===!1&&(n.depthTest=this.depthTest),this.depthWrite===!1&&(n.depthWrite=this.depthWrite),this.colorWrite===!1&&(n.colorWrite=this.colorWrite),this.stencilWriteMask!==255&&(n.stencilWriteMask=this.stencilWriteMask),this.stencilFunc!==wl&&(n.stencilFunc=this.stencilFunc),this.stencilRef!==0&&(n.stencilRef=this.stencilRef),this.stencilFuncMask!==255&&(n.stencilFuncMask=this.stencilFuncMask),this.stencilFail!==bi&&(n.stencilFail=this.stencilFail),this.stencilZFail!==bi&&(n.stencilZFail=this.stencilZFail),this.stencilZPass!==bi&&(n.stencilZPass=this.stencilZPass),this.stencilWrite===!0&&(n.stencilWrite=this.stencilWrite),this.rotation!==void 0&&this.rotation!==0&&(n.rotation=this.rotation),this.polygonOffset===!0&&(n.polygonOffset=!0),this.polygonOffsetFactor!==0&&(n.polygonOffsetFactor=this.polygonOffsetFactor),this.polygonOffsetUnits!==0&&(n.polygonOffsetUnits=this.polygonOffsetUnits),this.linewidth!==void 0&&this.linewidth!==1&&(n.linewidth=this.linewidth),this.dashSize!==void 0&&(n.dashSize=this.dashSize),this.gapSize!==void 0&&(n.gapSize=this.gapSize),this.scale!==void 0&&(n.scale=this.scale),this.dithering===!0&&(n.dithering=!0),this.alphaTest>0&&(n.alphaTest=this.alphaTest),this.alphaHash===!0&&(n.alphaHash=!0),this.alphaToCoverage===!0&&(n.alphaToCoverage=!0),this.premultipliedAlpha===!0&&(n.premultipliedAlpha=!0),this.forceSinglePass===!0&&(n.forceSinglePass=!0),this.wireframe===!0&&(n.wireframe=!0),this.wireframeLinewidth>1&&(n.wireframeLinewidth=this.wireframeLinewidth),this.wireframeLinecap!=="round"&&(n.wireframeLinecap=this.wireframeLinecap),this.wireframeLinejoin!=="round"&&(n.wireframeLinejoin=this.wireframeLinejoin),this.flatShading===!0&&(n.flatShading=!0),this.visible===!1&&(n.visible=!1),this.toneMapped===!1&&(n.toneMapped=!1),this.fog===!1&&(n.fog=!1),Object.keys(this.userData).length>0&&(n.userData=this.userData);function r(s){let a=[];for(let o in s){let l=s[o];delete l.metadata,a.push(l)}return a}if(t){let s=r(e.textures),a=r(e.images);s.length>0&&(n.textures=s),a.length>0&&(n.images=a)}return n}clone(){return new this.constructor().copy(this)}copy(e){this.name=e.name,this.blending=e.blending,this.side=e.side,this.vertexColors=e.vertexColors,this.opacity=e.opacity,this.transparent=e.transparent,this.blendSrc=e.blendSrc,this.blendDst=e.blendDst,this.blendEquation=e.blendEquation,this.blendSrcAlpha=e.blendSrcAlpha,this.blendDstAlpha=e.blendDstAlpha,this.blendEquationAlpha=e.blendEquationAlpha,this.blendColor.copy(e.blendColor),this.blendAlpha=e.blendAlpha,this.depthFunc=e.depthFunc,this.depthTest=e.depthTest,this.depthWrite=e.depthWrite,this.stencilWriteMask=e.stencilWriteMask,this.stencilFunc=e.stencilFunc,this.stencilRef=e.stencilRef,this.stencilFuncMask=e.stencilFuncMask,this.stencilFail=e.stencilFail,this.stencilZFail=e.stencilZFail,this.stencilZPass=e.stencilZPass,this.stencilWrite=e.stencilWrite;let t=e.clippingPlanes,n=null;if(t!==null){let r=t.length;n=new Array(r);for(let s=0;s!==r;++s)n[s]=t[s].clone()}return this.clippingPlanes=n,this.clipIntersection=e.clipIntersection,this.clipShadows=e.clipShadows,this.shadowSide=e.shadowSide,this.colorWrite=e.colorWrite,this.precision=e.precision,this.polygonOffset=e.polygonOffset,this.polygonOffsetFactor=e.polygonOffsetFactor,this.polygonOffsetUnits=e.polygonOffsetUnits,this.dithering=e.dithering,this.alphaTest=e.alphaTest,this.alphaHash=e.alphaHash,this.alphaToCoverage=e.alphaToCoverage,this.premultipliedAlpha=e.premultipliedAlpha,this.forceSinglePass=e.forceSinglePass,this.visible=e.visible,this.toneMapped=e.toneMapped,this.userData=JSON.parse(JSON.stringify(e.userData)),this}dispose(){this.dispatchEvent({type:"dispose"})}set needsUpdate(e){e===!0&&this.version++}},Xt=class extends bn{constructor(e){super(),this.isMeshBasicMaterial=!0,this.type="MeshBasicMaterial",this.color=new Ne(16777215),this.map=null,this.lightMap=null,this.lightMapIntensity=1,this.aoMap=null,this.aoMapIntensity=1,this.specularMap=null,this.alphaMap=null,this.envMap=null,this.envMapRotation=new en,this.combine=Nl,this.reflectivity=1,this.refractionRatio=.98,this.wireframe=!1,this.wireframeLinewidth=1,this.wireframeLinecap="round",this.wireframeLinejoin="round",this.fog=!0,this.setValues(e)}copy(e){return super.copy(e),this.color.copy(e.color),this.map=e.map,this.lightMap=e.lightMap,this.lightMapIntensity=e.lightMapIntensity,this.aoMap=e.aoMap,this.aoMapIntensity=e.aoMapIntensity,this.specularMap=e.specularMap,this.alphaMap=e.alphaMap,this.envMap=e.envMap,this.envMapRotation.copy(e.envMapRotation),this.combine=e.combine,this.reflectivity=e.reflectivity,this.refractionRatio=e.refractionRatio,this.wireframe=e.wireframe,this.wireframeLinewidth=e.wireframeLinewidth,this.wireframeLinecap=e.wireframeLinecap,this.wireframeLinejoin=e.wireframeLinejoin,this.fog=e.fog,this}};var bt=new N,Bs=new He,Qh=0,Gt=class{constructor(e,t,n=!1){if(Array.isArray(e))throw new TypeError("THREE.BufferAttribute: array should be a Typed Array.");this.isBufferAttribute=!0,Object.defineProperty(this,"id",{value:Qh++}),this.name="",this.array=e,this.itemSize=t,this.count=e!==void 0?e.length/t:0,this.normalized=n,this.usage=ua,this.updateRanges=[],this.gpuType=Pn,this.version=0}onUploadCallback(){}set needsUpdate(e){e===!0&&this.version++}setUsage(e){return this.usage=e,this}addUpdateRange(e,t){this.updateRanges.push({start:e,count:t})}clearUpdateRanges(){this.updateRanges.length=0}copy(e){return this.name=e.name,this.array=new e.array.constructor(e.array),this.itemSize=e.itemSize,this.count=e.count,this.normalized=e.normalized,this.usage=e.usage,this.gpuType=e.gpuType,this}copyAt(e,t,n){e*=this.itemSize,n*=t.itemSize;for(let r=0,s=this.itemSize;r<s;r++)this.array[e+r]=t.array[n+r];return this}copyArray(e){return this.array.set(e),this}applyMatrix3(e){if(this.itemSize===2)for(let t=0,n=this.count;t<n;t++)Bs.fromBufferAttribute(this,t),Bs.applyMatrix3(e),this.setXY(t,Bs.x,Bs.y);else if(this.itemSize===3)for(let t=0,n=this.count;t<n;t++)bt.fromBufferAttribute(this,t),bt.applyMatrix3(e),this.setXYZ(t,bt.x,bt.y,bt.z);return this}applyMatrix4(e){for(let t=0,n=this.count;t<n;t++)bt.fromBufferAttribute(this,t),bt.applyMatrix4(e),this.setXYZ(t,bt.x,bt.y,bt.z);return this}applyNormalMatrix(e){for(let t=0,n=this.count;t<n;t++)bt.fromBufferAttribute(this,t),bt.applyNormalMatrix(e),this.setXYZ(t,bt.x,bt.y,bt.z);return this}transformDirection(e){for(let t=0,n=this.count;t<n;t++)bt.fromBufferAttribute(this,t),bt.transformDirection(e),this.setXYZ(t,bt.x,bt.y,bt.z);return this}set(e,t=0){return this.array.set(e,t),this}getComponent(e,t){let n=this.array[e*this.itemSize+t];return this.normalized&&(n=_n(n,this.array)),n}setComponent(e,t,n){return this.normalized&&(n=Je(n,this.array)),this.array[e*this.itemSize+t]=n,this}getX(e){let t=this.array[e*this.itemSize];return this.normalized&&(t=_n(t,this.array)),t}setX(e,t){return this.normalized&&(t=Je(t,this.array)),this.array[e*this.itemSize]=t,this}getY(e){let t=this.array[e*this.itemSize+1];return this.normalized&&(t=_n(t,this.array)),t}setY(e,t){return this.normalized&&(t=Je(t,this.array)),this.array[e*this.itemSize+1]=t,this}getZ(e){let t=this.array[e*this.itemSize+2];return this.normalized&&(t=_n(t,this.array)),t}setZ(e,t){return this.normalized&&(t=Je(t,this.array)),this.array[e*this.itemSize+2]=t,this}getW(e){let t=this.array[e*this.itemSize+3];return this.normalized&&(t=_n(t,this.array)),t}setW(e,t){return this.normalized&&(t=Je(t,this.array)),this.array[e*this.itemSize+3]=t,this}setXY(e,t,n){return e*=this.itemSize,this.normalized&&(t=Je(t,this.array),n=Je(n,this.array)),this.array[e+0]=t,this.array[e+1]=n,this}setXYZ(e,t,n,r){return e*=this.itemSize,this.normalized&&(t=Je(t,this.array),n=Je(n,this.array),r=Je(r,this.array)),this.array[e+0]=t,this.array[e+1]=n,this.array[e+2]=r,this}setXYZW(e,t,n,r,s){return e*=this.itemSize,this.normalized&&(t=Je(t,this.array),n=Je(n,this.array),r=Je(r,this.array),s=Je(s,this.array)),this.array[e+0]=t,this.array[e+1]=n,this.array[e+2]=r,this.array[e+3]=s,this}onUpload(e){return this.onUploadCallback=e,this}clone(){return new this.constructor(this.array,this.itemSize).copy(this)}toJSON(){let e={itemSize:this.itemSize,type:this.array.constructor.name,array:Array.from(this.array),normalized:this.normalized};return this.name!==""&&(e.name=this.name),this.usage!==ua&&(e.usage=this.usage),e}};var Xr=class extends Gt{constructor(e,t,n){super(new Uint16Array(e),t,n)}};var $r=class extends Gt{constructor(e,t,n){super(new Uint32Array(e),t,n)}};var je=class extends Gt{constructor(e,t,n){super(new Float32Array(e),t,n)}},ef=0,ln=new ct,ul=new wt,ji=new N,Qt=new si,Dr=new si,Ct=new N,dt=class i extends Gn{constructor(){super(),this.isBufferGeometry=!0,Object.defineProperty(this,"id",{value:ef++}),this.uuid=kn(),this.name="",this.type="BufferGeometry",this.index=null,this.indirect=null,this.attributes={},this.morphAttributes={},this.morphTargetsRelative=!1,this.groups=[],this.boundingBox=null,this.boundingSphere=null,this.drawRange={start:0,count:1/0},this.userData={}}getIndex(){return this.index}setIndex(e){return Array.isArray(e)?this.index=new($l(e)?$r:Xr)(e,1):this.index=e,this}setIndirect(e){return this.indirect=e,this}getIndirect(){return this.indirect}getAttribute(e){return this.attributes[e]}setAttribute(e,t){return this.attributes[e]=t,this}deleteAttribute(e){return delete this.attributes[e],this}hasAttribute(e){return this.attributes[e]!==void 0}addGroup(e,t,n=0){this.groups.push({start:e,count:t,materialIndex:n})}clearGroups(){this.groups=[]}setDrawRange(e,t){this.drawRange.start=e,this.drawRange.count=t}applyMatrix4(e){let t=this.attributes.position;t!==void 0&&(t.applyMatrix4(e),t.needsUpdate=!0);let n=this.attributes.normal;if(n!==void 0){let s=new Oe().getNormalMatrix(e);n.applyNormalMatrix(s),n.needsUpdate=!0}let r=this.attributes.tangent;return r!==void 0&&(r.transformDirection(e),r.needsUpdate=!0),this.boundingBox!==null&&this.computeBoundingBox(),this.boundingSphere!==null&&this.computeBoundingSphere(),this}applyQuaternion(e){return ln.makeRotationFromQuaternion(e),this.applyMatrix4(ln),this}rotateX(e){return ln.makeRotationX(e),this.applyMatrix4(ln),this}rotateY(e){return ln.makeRotationY(e),this.applyMatrix4(ln),this}rotateZ(e){return ln.makeRotationZ(e),this.applyMatrix4(ln),this}translate(e,t,n){return ln.makeTranslation(e,t,n),this.applyMatrix4(ln),this}scale(e,t,n){return ln.makeScale(e,t,n),this.applyMatrix4(ln),this}lookAt(e){return ul.lookAt(e),ul.updateMatrix(),this.applyMatrix4(ul.matrix),this}center(){return this.computeBoundingBox(),this.boundingBox.getCenter(ji).negate(),this.translate(ji.x,ji.y,ji.z),this}setFromPoints(e){let t=this.getAttribute("position");if(t===void 0){let n=[];for(let r=0,s=e.length;r<s;r++){let a=e[r];n.push(a.x,a.y,a.z||0)}this.setAttribute("position",new je(n,3))}else{let n=Math.min(e.length,t.count);for(let r=0;r<n;r++){let s=e[r];t.setXYZ(r,s.x,s.y,s.z||0)}e.length>t.count&&console.warn("THREE.BufferGeometry: Buffer size too small for points data. Use .dispose() and create a new geometry."),t.needsUpdate=!0}return this}computeBoundingBox(){this.boundingBox===null&&(this.boundingBox=new si);let e=this.attributes.position,t=this.morphAttributes.position;if(e&&e.isGLBufferAttribute){console.error("THREE.BufferGeometry.computeBoundingBox(): GLBufferAttribute requires a manual bounding box.",this),this.boundingBox.set(new N(-1/0,-1/0,-1/0),new N(1/0,1/0,1/0));return}if(e!==void 0){if(this.boundingBox.setFromBufferAttribute(e),t)for(let n=0,r=t.length;n<r;n++){let s=t[n];Qt.setFromBufferAttribute(s),this.morphTargetsRelative?(Ct.addVectors(this.boundingBox.min,Qt.min),this.boundingBox.expandByPoint(Ct),Ct.addVectors(this.boundingBox.max,Qt.max),this.boundingBox.expandByPoint(Ct)):(this.boundingBox.expandByPoint(Qt.min),this.boundingBox.expandByPoint(Qt.max))}}else this.boundingBox.makeEmpty();(isNaN(this.boundingBox.min.x)||isNaN(this.boundingBox.min.y)||isNaN(this.boundingBox.min.z))&&console.error('THREE.BufferGeometry.computeBoundingBox(): Computed min/max have NaN values. The "position" attribute is likely to have NaN values.',this)}computeBoundingSphere(){this.boundingSphere===null&&(this.boundingSphere=new ai);let e=this.attributes.position,t=this.morphAttributes.position;if(e&&e.isGLBufferAttribute){console.error("THREE.BufferGeometry.computeBoundingSphere(): GLBufferAttribute requires a manual bounding sphere.",this),this.boundingSphere.set(new N,1/0);return}if(e){let n=this.boundingSphere.center;if(Qt.setFromBufferAttribute(e),t)for(let s=0,a=t.length;s<a;s++){let o=t[s];Dr.setFromBufferAttribute(o),this.morphTargetsRelative?(Ct.addVectors(Qt.min,Dr.min),Qt.expandByPoint(Ct),Ct.addVectors(Qt.max,Dr.max),Qt.expandByPoint(Ct)):(Qt.expandByPoint(Dr.min),Qt.expandByPoint(Dr.max))}Qt.getCenter(n);let r=0;for(let s=0,a=e.count;s<a;s++)Ct.fromBufferAttribute(e,s),r=Math.max(r,n.distanceToSquared(Ct));if(t)for(let s=0,a=t.length;s<a;s++){let o=t[s],l=this.morphTargetsRelative;for(let c=0,d=o.count;c<d;c++)Ct.fromBufferAttribute(o,c),l&&(ji.fromBufferAttribute(e,c),Ct.add(ji)),r=Math.max(r,n.distanceToSquared(Ct))}this.boundingSphere.radius=Math.sqrt(r),isNaN(this.boundingSphere.radius)&&console.error('THREE.BufferGeometry.computeBoundingSphere(): Computed radius is NaN. The "position" attribute is likely to have NaN values.',this)}}computeTangents(){let e=this.index,t=this.attributes;if(e===null||t.position===void 0||t.normal===void 0||t.uv===void 0){console.error("THREE.BufferGeometry: .computeTangents() failed. Missing required attributes (index, position, normal or uv)");return}let n=t.position,r=t.normal,s=t.uv;this.hasAttribute("tangent")===!1&&this.setAttribute("tangent",new Gt(new Float32Array(4*n.count),4));let a=this.getAttribute("tangent"),o=[],l=[];for(let P=0;P<n.count;P++)o[P]=new N,l[P]=new N;let c=new N,d=new N,u=new N,h=new He,p=new He,g=new He,x=new N,m=new N;function f(P,w,v){c.fromBufferAttribute(n,P),d.fromBufferAttribute(n,w),u.fromBufferAttribute(n,v),h.fromBufferAttribute(s,P),p.fromBufferAttribute(s,w),g.fromBufferAttribute(s,v),d.sub(c),u.sub(c),p.sub(h),g.sub(h);let T=1/(p.x*g.y-g.x*p.y);isFinite(T)&&(x.copy(d).multiplyScalar(g.y).addScaledVector(u,-p.y).multiplyScalar(T),m.copy(u).multiplyScalar(p.x).addScaledVector(d,-g.x).multiplyScalar(T),o[P].add(x),o[w].add(x),o[v].add(x),l[P].add(m),l[w].add(m),l[v].add(m))}let S=this.groups;S.length===0&&(S=[{start:0,count:e.count}]);for(let P=0,w=S.length;P<w;++P){let v=S[P],T=v.start,D=v.count;for(let F=T,B=T+D;F<B;F+=3)f(e.getX(F+0),e.getX(F+1),e.getX(F+2))}let M=new N,y=new N,C=new N,E=new N;function R(P){C.fromBufferAttribute(r,P),E.copy(C);let w=o[P];M.copy(w),M.sub(C.multiplyScalar(C.dot(w))).normalize(),y.crossVectors(E,w);let T=y.dot(l[P])<0?-1:1;a.setXYZW(P,M.x,M.y,M.z,T)}for(let P=0,w=S.length;P<w;++P){let v=S[P],T=v.start,D=v.count;for(let F=T,B=T+D;F<B;F+=3)R(e.getX(F+0)),R(e.getX(F+1)),R(e.getX(F+2))}}computeVertexNormals(){let e=this.index,t=this.getAttribute("position");if(t!==void 0){let n=this.getAttribute("normal");if(n===void 0)n=new Gt(new Float32Array(t.count*3),3),this.setAttribute("normal",n);else for(let h=0,p=n.count;h<p;h++)n.setXYZ(h,0,0,0);let r=new N,s=new N,a=new N,o=new N,l=new N,c=new N,d=new N,u=new N;if(e)for(let h=0,p=e.count;h<p;h+=3){let g=e.getX(h+0),x=e.getX(h+1),m=e.getX(h+2);r.fromBufferAttribute(t,g),s.fromBufferAttribute(t,x),a.fromBufferAttribute(t,m),d.subVectors(a,s),u.subVectors(r,s),d.cross(u),o.fromBufferAttribute(n,g),l.fromBufferAttribute(n,x),c.fromBufferAttribute(n,m),o.add(d),l.add(d),c.add(d),n.setXYZ(g,o.x,o.y,o.z),n.setXYZ(x,l.x,l.y,l.z),n.setXYZ(m,c.x,c.y,c.z)}else for(let h=0,p=t.count;h<p;h+=3)r.fromBufferAttribute(t,h+0),s.fromBufferAttribute(t,h+1),a.fromBufferAttribute(t,h+2),d.subVectors(a,s),u.subVectors(r,s),d.cross(u),n.setXYZ(h+0,d.x,d.y,d.z),n.setXYZ(h+1,d.x,d.y,d.z),n.setXYZ(h+2,d.x,d.y,d.z);this.normalizeNormals(),n.needsUpdate=!0}}normalizeNormals(){let e=this.attributes.normal;for(let t=0,n=e.count;t<n;t++)Ct.fromBufferAttribute(e,t),Ct.normalize(),e.setXYZ(t,Ct.x,Ct.y,Ct.z)}toNonIndexed(){function e(o,l){let c=o.array,d=o.itemSize,u=o.normalized,h=new c.constructor(l.length*d),p=0,g=0;for(let x=0,m=l.length;x<m;x++){o.isInterleavedBufferAttribute?p=l[x]*o.data.stride+o.offset:p=l[x]*d;for(let f=0;f<d;f++)h[g++]=c[p++]}return new Gt(h,d,u)}if(this.index===null)return console.warn("THREE.BufferGeometry.toNonIndexed(): BufferGeometry is already non-indexed."),this;let t=new i,n=this.index.array,r=this.attributes;for(let o in r){let l=r[o],c=e(l,n);t.setAttribute(o,c)}let s=this.morphAttributes;for(let o in s){let l=[],c=s[o];for(let d=0,u=c.length;d<u;d++){let h=c[d],p=e(h,n);l.push(p)}t.morphAttributes[o]=l}t.morphTargetsRelative=this.morphTargetsRelative;let a=this.groups;for(let o=0,l=a.length;o<l;o++){let c=a[o];t.addGroup(c.start,c.count,c.materialIndex)}return t}toJSON(){let e={metadata:{version:4.7,type:"BufferGeometry",generator:"BufferGeometry.toJSON"}};if(e.uuid=this.uuid,e.type=this.type,this.name!==""&&(e.name=this.name),Object.keys(this.userData).length>0&&(e.userData=this.userData),this.parameters!==void 0){let l=this.parameters;for(let c in l)l[c]!==void 0&&(e[c]=l[c]);return e}e.data={attributes:{}};let t=this.index;t!==null&&(e.data.index={type:t.array.constructor.name,array:Array.prototype.slice.call(t.array)});let n=this.attributes;for(let l in n){let c=n[l];e.data.attributes[l]=c.toJSON(e.data)}let r={},s=!1;for(let l in this.morphAttributes){let c=this.morphAttributes[l],d=[];for(let u=0,h=c.length;u<h;u++){let p=c[u];d.push(p.toJSON(e.data))}d.length>0&&(r[l]=d,s=!0)}s&&(e.data.morphAttributes=r,e.data.morphTargetsRelative=this.morphTargetsRelative);let a=this.groups;a.length>0&&(e.data.groups=JSON.parse(JSON.stringify(a)));let o=this.boundingSphere;return o!==null&&(e.data.boundingSphere=o.toJSON()),e}clone(){return new this.constructor().copy(this)}copy(e){this.index=null,this.attributes={},this.morphAttributes={},this.groups=[],this.boundingBox=null,this.boundingSphere=null;let t={};this.name=e.name;let n=e.index;n!==null&&this.setIndex(n.clone());let r=e.attributes;for(let c in r){let d=r[c];this.setAttribute(c,d.clone(t))}let s=e.morphAttributes;for(let c in s){let d=[],u=s[c];for(let h=0,p=u.length;h<p;h++)d.push(u[h].clone(t));this.morphAttributes[c]=d}this.morphTargetsRelative=e.morphTargetsRelative;let a=e.groups;for(let c=0,d=a.length;c<d;c++){let u=a[c];this.addGroup(u.start,u.count,u.materialIndex)}let o=e.boundingBox;o!==null&&(this.boundingBox=o.clone());let l=e.boundingSphere;return l!==null&&(this.boundingSphere=l.clone()),this.drawRange.start=e.drawRange.start,this.drawRange.count=e.drawRange.count,this.userData=e.userData,this}dispose(){this.dispatchEvent({type:"dispose"})}},Kc=new ct,yi=new ur,zs=new ai,jc=new N,ks=new N,Hs=new N,Vs=new N,hl=new N,Gs=new N,Qc=new N,Ws=new N,st=class extends wt{constructor(e=new dt,t=new Xt){super(),this.isMesh=!0,this.type="Mesh",this.geometry=e,this.material=t,this.morphTargetDictionary=void 0,this.morphTargetInfluences=void 0,this.count=1,this.updateMorphTargets()}copy(e,t){return super.copy(e,t),e.morphTargetInfluences!==void 0&&(this.morphTargetInfluences=e.morphTargetInfluences.slice()),e.morphTargetDictionary!==void 0&&(this.morphTargetDictionary=Object.assign({},e.morphTargetDictionary)),this.material=Array.isArray(e.material)?e.material.slice():e.material,this.geometry=e.geometry,this}updateMorphTargets(){let t=this.geometry.morphAttributes,n=Object.keys(t);if(n.length>0){let r=t[n[0]];if(r!==void 0){this.morphTargetInfluences=[],this.morphTargetDictionary={};for(let s=0,a=r.length;s<a;s++){let o=r[s].name||String(s);this.morphTargetInfluences.push(0),this.morphTargetDictionary[o]=s}}}}getVertexPosition(e,t){let n=this.geometry,r=n.attributes.position,s=n.morphAttributes.position,a=n.morphTargetsRelative;t.fromBufferAttribute(r,e);let o=this.morphTargetInfluences;if(s&&o){Gs.set(0,0,0);for(let l=0,c=s.length;l<c;l++){let d=o[l],u=s[l];d!==0&&(hl.fromBufferAttribute(u,e),a?Gs.addScaledVector(hl,d):Gs.addScaledVector(hl.sub(t),d))}t.add(Gs)}return t}raycast(e,t){let n=this.geometry,r=this.material,s=this.matrixWorld;r!==void 0&&(n.boundingSphere===null&&n.computeBoundingSphere(),zs.copy(n.boundingSphere),zs.applyMatrix4(s),yi.copy(e.ray).recast(e.near),!(zs.containsPoint(yi.origin)===!1&&(yi.intersectSphere(zs,jc)===null||yi.origin.distanceToSquared(jc)>(e.far-e.near)**2))&&(Kc.copy(s).invert(),yi.copy(e.ray).applyMatrix4(Kc),!(n.boundingBox!==null&&yi.intersectsBox(n.boundingBox)===!1)&&this._computeIntersections(e,t,yi)))}_computeIntersections(e,t,n){let r,s=this.geometry,a=this.material,o=s.index,l=s.attributes.position,c=s.attributes.uv,d=s.attributes.uv1,u=s.attributes.normal,h=s.groups,p=s.drawRange;if(o!==null)if(Array.isArray(a))for(let g=0,x=h.length;g<x;g++){let m=h[g],f=a[m.materialIndex],S=Math.max(m.start,p.start),M=Math.min(o.count,Math.min(m.start+m.count,p.start+p.count));for(let y=S,C=M;y<C;y+=3){let E=o.getX(y),R=o.getX(y+1),P=o.getX(y+2);r=Xs(this,f,e,n,c,d,u,E,R,P),r&&(r.faceIndex=Math.floor(y/3),r.face.materialIndex=m.materialIndex,t.push(r))}}else{let g=Math.max(0,p.start),x=Math.min(o.count,p.start+p.count);for(let m=g,f=x;m<f;m+=3){let S=o.getX(m),M=o.getX(m+1),y=o.getX(m+2);r=Xs(this,a,e,n,c,d,u,S,M,y),r&&(r.faceIndex=Math.floor(m/3),t.push(r))}}else if(l!==void 0)if(Array.isArray(a))for(let g=0,x=h.length;g<x;g++){let m=h[g],f=a[m.materialIndex],S=Math.max(m.start,p.start),M=Math.min(l.count,Math.min(m.start+m.count,p.start+p.count));for(let y=S,C=M;y<C;y+=3){let E=y,R=y+1,P=y+2;r=Xs(this,f,e,n,c,d,u,E,R,P),r&&(r.faceIndex=Math.floor(y/3),r.face.materialIndex=m.materialIndex,t.push(r))}}else{let g=Math.max(0,p.start),x=Math.min(l.count,p.start+p.count);for(let m=g,f=x;m<f;m+=3){let S=m,M=m+1,y=m+2;r=Xs(this,a,e,n,c,d,u,S,M,y),r&&(r.faceIndex=Math.floor(m/3),t.push(r))}}}};function tf(i,e,t,n,r,s,a,o){let l;if(e.side===zt?l=n.intersectTriangle(a,s,r,!0,o):l=n.intersectTriangle(r,s,a,e.side===Vn,o),l===null)return null;Ws.copy(o),Ws.applyMatrix4(i.matrixWorld);let c=t.ray.origin.distanceTo(Ws);return c<t.near||c>t.far?null:{distance:c,point:Ws.clone(),object:i}}function Xs(i,e,t,n,r,s,a,o,l,c){i.getVertexPosition(o,ks),i.getVertexPosition(l,Hs),i.getVertexPosition(c,Vs);let d=tf(i,e,t,n,ks,Hs,Vs,Qc);if(d){let u=new N;An.getBarycoord(Qc,ks,Hs,Vs,u),r&&(d.uv=An.getInterpolatedAttribute(r,o,l,c,u,new He)),s&&(d.uv1=An.getInterpolatedAttribute(s,o,l,c,u,new He)),a&&(d.normal=An.getInterpolatedAttribute(a,o,l,c,u,new N),d.normal.dot(n.direction)>0&&d.normal.multiplyScalar(-1));let h={a:o,b:l,c,normal:new N,materialIndex:0};An.getNormal(ks,Hs,Vs,h.normal),d.face=h,d.barycoord=u}return d}var wn=class i extends dt{constructor(e=1,t=1,n=1,r=1,s=1,a=1){super(),this.type="BoxGeometry",this.parameters={width:e,height:t,depth:n,widthSegments:r,heightSegments:s,depthSegments:a};let o=this;r=Math.floor(r),s=Math.floor(s),a=Math.floor(a);let l=[],c=[],d=[],u=[],h=0,p=0;g("z","y","x",-1,-1,n,t,e,a,s,0),g("z","y","x",1,-1,n,t,-e,a,s,1),g("x","z","y",1,1,e,n,t,r,a,2),g("x","z","y",1,-1,e,n,-t,r,a,3),g("x","y","z",1,-1,e,t,n,r,s,4),g("x","y","z",-1,-1,e,t,-n,r,s,5),this.setIndex(l),this.setAttribute("position",new je(c,3)),this.setAttribute("normal",new je(d,3)),this.setAttribute("uv",new je(u,2));function g(x,m,f,S,M,y,C,E,R,P,w){let v=y/R,T=C/P,D=y/2,F=C/2,B=E/2,k=R+1,W=P+1,X=0,H=0,Q=new N;for(let ne=0;ne<W;ne++){let fe=ne*T-F;for(let De=0;De<k;De++){let Xe=De*v-D;Q[x]=Xe*S,Q[m]=fe*M,Q[f]=B,c.push(Q.x,Q.y,Q.z),Q[x]=0,Q[m]=0,Q[f]=E>0?1:-1,d.push(Q.x,Q.y,Q.z),u.push(De/R),u.push(1-ne/P),X+=1}}for(let ne=0;ne<P;ne++)for(let fe=0;fe<R;fe++){let De=h+fe+k*ne,Xe=h+fe+k*(ne+1),Ze=h+(fe+1)+k*(ne+1),Fe=h+(fe+1)+k*ne;l.push(De,Xe,Fe),l.push(Xe,Ze,Fe),H+=6}o.addGroup(p,H,w),p+=H,h+=X}}copy(e){return super.copy(e),this.parameters=Object.assign({},e.parameters),this}static fromJSON(e){return new i(e.width,e.height,e.depth,e.widthSegments,e.heightSegments,e.depthSegments)}};function Ri(i){let e={};for(let t in i){e[t]={};for(let n in i[t]){let r=i[t][n];r&&(r.isColor||r.isMatrix3||r.isMatrix4||r.isVector2||r.isVector3||r.isVector4||r.isTexture||r.isQuaternion)?r.isRenderTargetTexture?(console.warn("UniformsUtils: Textures of render targets cannot be cloned via cloneUniforms() or mergeUniforms()."),e[t][n]=null):e[t][n]=r.clone():Array.isArray(r)?e[t][n]=r.slice():e[t][n]=r}}return e}function Ft(i){let e={};for(let t=0;t<i.length;t++){let n=Ri(i[t]);for(let r in n)e[r]=n[r]}return e}function nf(i){let e=[];for(let t=0;t<i.length;t++)e.push(i[t].clone());return e}function ql(i){let e=i.getRenderTarget();return e===null?i.outputColorSpace:e.isXRRenderTarget===!0?e.texture.colorSpace:$e.workingColorSpace}var iu={clone:Ri,merge:Ft},rf=`void main() {
	gl_Position = projectionMatrix * modelViewMatrix * vec4( position, 1.0 );
}`,sf=`void main() {
	gl_FragColor = vec4( 1.0, 0.0, 0.0, 1.0 );
}`,tn=class extends bn{constructor(e){super(),this.isShaderMaterial=!0,this.type="ShaderMaterial",this.defines={},this.uniforms={},this.uniformsGroups=[],this.vertexShader=rf,this.fragmentShader=sf,this.linewidth=1,this.wireframe=!1,this.wireframeLinewidth=1,this.fog=!1,this.lights=!1,this.clipping=!1,this.forceSinglePass=!0,this.extensions={clipCullDistance:!1,multiDraw:!1},this.defaultAttributeValues={color:[1,1,1],uv:[0,0],uv1:[0,0]},this.index0AttributeName=void 0,this.uniformsNeedUpdate=!1,this.glslVersion=null,e!==void 0&&this.setValues(e)}copy(e){return super.copy(e),this.fragmentShader=e.fragmentShader,this.vertexShader=e.vertexShader,this.uniforms=Ri(e.uniforms),this.uniformsGroups=nf(e.uniformsGroups),this.defines=Object.assign({},e.defines),this.wireframe=e.wireframe,this.wireframeLinewidth=e.wireframeLinewidth,this.fog=e.fog,this.lights=e.lights,this.clipping=e.clipping,this.extensions=Object.assign({},e.extensions),this.glslVersion=e.glslVersion,this}toJSON(e){let t=super.toJSON(e);t.glslVersion=this.glslVersion,t.uniforms={};for(let r in this.uniforms){let a=this.uniforms[r].value;a&&a.isTexture?t.uniforms[r]={type:"t",value:a.toJSON(e).uuid}:a&&a.isColor?t.uniforms[r]={type:"c",value:a.getHex()}:a&&a.isVector2?t.uniforms[r]={type:"v2",value:a.toArray()}:a&&a.isVector3?t.uniforms[r]={type:"v3",value:a.toArray()}:a&&a.isVector4?t.uniforms[r]={type:"v4",value:a.toArray()}:a&&a.isMatrix3?t.uniforms[r]={type:"m3",value:a.toArray()}:a&&a.isMatrix4?t.uniforms[r]={type:"m4",value:a.toArray()}:t.uniforms[r]={value:a}}Object.keys(this.defines).length>0&&(t.defines=this.defines),t.vertexShader=this.vertexShader,t.fragmentShader=this.fragmentShader,t.lights=this.lights,t.clipping=this.clipping;let n={};for(let r in this.extensions)this.extensions[r]===!0&&(n[r]=!0);return Object.keys(n).length>0&&(t.extensions=n),t}},qr=class extends wt{constructor(){super(),this.isCamera=!0,this.type="Camera",this.matrixWorldInverse=new ct,this.projectionMatrix=new ct,this.projectionMatrixInverse=new ct,this.coordinateSystem=yn,this._reversedDepth=!1}get reversedDepth(){return this._reversedDepth}copy(e,t){return super.copy(e,t),this.matrixWorldInverse.copy(e.matrixWorldInverse),this.projectionMatrix.copy(e.projectionMatrix),this.projectionMatrixInverse.copy(e.projectionMatrixInverse),this.coordinateSystem=e.coordinateSystem,this}getWorldDirection(e){return super.getWorldDirection(e).negate()}updateMatrixWorld(e){super.updateMatrixWorld(e),this.matrixWorldInverse.copy(this.matrixWorld).invert()}updateWorldMatrix(e,t){super.updateWorldMatrix(e,t),this.matrixWorldInverse.copy(this.matrixWorld).invert()}clone(){return new this.constructor().copy(this)}},ni=new N,ed=new He,td=new He,Dt=class extends qr{constructor(e=50,t=1,n=.1,r=2e3){super(),this.isPerspectiveCamera=!0,this.type="PerspectiveCamera",this.fov=e,this.zoom=1,this.near=n,this.far=r,this.focus=10,this.aspect=t,this.view=null,this.filmGauge=35,this.filmOffset=0,this.updateProjectionMatrix()}copy(e,t){return super.copy(e,t),this.fov=e.fov,this.zoom=e.zoom,this.near=e.near,this.far=e.far,this.focus=e.focus,this.aspect=e.aspect,this.view=e.view===null?null:Object.assign({},e.view),this.filmGauge=e.filmGauge,this.filmOffset=e.filmOffset,this}setFocalLength(e){let t=.5*this.getFilmHeight()/e;this.fov=lr*2*Math.atan(t),this.updateProjectionMatrix()}getFocalLength(){let e=Math.tan(sr*.5*this.fov);return .5*this.getFilmHeight()/e}getEffectiveFOV(){return lr*2*Math.atan(Math.tan(sr*.5*this.fov)/this.zoom)}getFilmWidth(){return this.filmGauge*Math.min(this.aspect,1)}getFilmHeight(){return this.filmGauge/Math.max(this.aspect,1)}getViewBounds(e,t,n){ni.set(-1,-1,.5).applyMatrix4(this.projectionMatrixInverse),t.set(ni.x,ni.y).multiplyScalar(-e/ni.z),ni.set(1,1,.5).applyMatrix4(this.projectionMatrixInverse),n.set(ni.x,ni.y).multiplyScalar(-e/ni.z)}getViewSize(e,t){return this.getViewBounds(e,ed,td),t.subVectors(td,ed)}setViewOffset(e,t,n,r,s,a){this.aspect=e/t,this.view===null&&(this.view={enabled:!0,fullWidth:1,fullHeight:1,offsetX:0,offsetY:0,width:1,height:1}),this.view.enabled=!0,this.view.fullWidth=e,this.view.fullHeight=t,this.view.offsetX=n,this.view.offsetY=r,this.view.width=s,this.view.height=a,this.updateProjectionMatrix()}clearViewOffset(){this.view!==null&&(this.view.enabled=!1),this.updateProjectionMatrix()}updateProjectionMatrix(){let e=this.near,t=e*Math.tan(sr*.5*this.fov)/this.zoom,n=2*t,r=this.aspect*n,s=-.5*r,a=this.view;if(this.view!==null&&this.view.enabled){let l=a.fullWidth,c=a.fullHeight;s+=a.offsetX*r/l,t-=a.offsetY*n/c,r*=a.width/l,n*=a.height/c}let o=this.filmOffset;o!==0&&(s+=e*o/this.getFilmWidth()),this.projectionMatrix.makePerspective(s,s+r,t,t-n,e,this.far,this.coordinateSystem,this.reversedDepth),this.projectionMatrixInverse.copy(this.projectionMatrix).invert()}toJSON(e){let t=super.toJSON(e);return t.object.fov=this.fov,t.object.zoom=this.zoom,t.object.near=this.near,t.object.far=this.far,t.object.focus=this.focus,t.object.aspect=this.aspect,this.view!==null&&(t.object.view=Object.assign({},this.view)),t.object.filmGauge=this.filmGauge,t.object.filmOffset=this.filmOffset,t}},Qi=-90,er=1,ma=class extends wt{constructor(e,t,n){super(),this.type="CubeCamera",this.renderTarget=n,this.coordinateSystem=null,this.activeMipmapLevel=0;let r=new Dt(Qi,er,e,t);r.layers=this.layers,this.add(r);let s=new Dt(Qi,er,e,t);s.layers=this.layers,this.add(s);let a=new Dt(Qi,er,e,t);a.layers=this.layers,this.add(a);let o=new Dt(Qi,er,e,t);o.layers=this.layers,this.add(o);let l=new Dt(Qi,er,e,t);l.layers=this.layers,this.add(l);let c=new Dt(Qi,er,e,t);c.layers=this.layers,this.add(c)}updateCoordinateSystem(){let e=this.coordinateSystem,t=this.children.concat(),[n,r,s,a,o,l]=t;for(let c of t)this.remove(c);if(e===yn)n.up.set(0,1,0),n.lookAt(1,0,0),r.up.set(0,1,0),r.lookAt(-1,0,0),s.up.set(0,0,-1),s.lookAt(0,1,0),a.up.set(0,0,1),a.lookAt(0,-1,0),o.up.set(0,1,0),o.lookAt(0,0,1),l.up.set(0,1,0),l.lookAt(0,0,-1);else if(e===Hr)n.up.set(0,-1,0),n.lookAt(-1,0,0),r.up.set(0,-1,0),r.lookAt(1,0,0),s.up.set(0,0,1),s.lookAt(0,1,0),a.up.set(0,0,-1),a.lookAt(0,-1,0),o.up.set(0,-1,0),o.lookAt(0,0,1),l.up.set(0,-1,0),l.lookAt(0,0,-1);else throw new Error("THREE.CubeCamera.updateCoordinateSystem(): Invalid coordinate system: "+e);for(let c of t)this.add(c),c.updateMatrixWorld()}update(e,t){this.parent===null&&this.updateMatrixWorld();let{renderTarget:n,activeMipmapLevel:r}=this;this.coordinateSystem!==e.coordinateSystem&&(this.coordinateSystem=e.coordinateSystem,this.updateCoordinateSystem());let[s,a,o,l,c,d]=this.children,u=e.getRenderTarget(),h=e.getActiveCubeFace(),p=e.getActiveMipmapLevel(),g=e.xr.enabled;e.xr.enabled=!1;let x=n.texture.generateMipmaps;n.texture.generateMipmaps=!1,e.setRenderTarget(n,0,r),e.render(t,s),e.setRenderTarget(n,1,r),e.render(t,a),e.setRenderTarget(n,2,r),e.render(t,o),e.setRenderTarget(n,3,r),e.render(t,l),e.setRenderTarget(n,4,r),e.render(t,c),n.texture.generateMipmaps=x,e.setRenderTarget(n,5,r),e.render(t,d),e.setRenderTarget(u,h,p),e.xr.enabled=g,n.texture.needsPMREMUpdate=!0}},Yr=class extends Lt{constructor(e=[],t=Ai,n,r,s,a,o,l,c,d){super(e,t,n,r,s,a,o,l,c,d),this.isCubeTexture=!0,this.flipY=!1}get images(){return this.image}set images(e){this.image=e}},ga=class extends Cn{constructor(e=1,t={}){super(e,e,t),this.isWebGLCubeRenderTarget=!0;let n={width:e,height:e,depth:1},r=[n,n,n,n,n,n];this.texture=new Yr(r),this._setTextureOptions(t),this.texture.isRenderTargetTexture=!0}fromEquirectangularTexture(e,t){this.texture.type=t.type,this.texture.colorSpace=t.colorSpace,this.texture.generateMipmaps=t.generateMipmaps,this.texture.minFilter=t.minFilter,this.texture.magFilter=t.magFilter;let n={uniforms:{tEquirect:{value:null}},vertexShader:`

				varying vec3 vWorldDirection;

				vec3 transformDirection( in vec3 dir, in mat4 matrix ) {

					return normalize( ( matrix * vec4( dir, 0.0 ) ).xyz );

				}

				void main() {

					vWorldDirection = transformDirection( position, modelMatrix );

					#include <begin_vertex>
					#include <project_vertex>

				}
			`,fragmentShader:`

				uniform sampler2D tEquirect;

				varying vec3 vWorldDirection;

				#include <common>

				void main() {

					vec3 direction = normalize( vWorldDirection );

					vec2 sampleUV = equirectUv( direction );

					gl_FragColor = texture2D( tEquirect, sampleUV );

				}
			`},r=new wn(5,5,5),s=new tn({name:"CubemapFromEquirect",uniforms:Ri(n.uniforms),vertexShader:n.vertexShader,fragmentShader:n.fragmentShader,side:zt,blending:Xn});s.uniforms.tEquirect.value=t;let a=new st(r,s),o=t.minFilter;return t.minFilter===ui&&(t.minFilter=vn),new ma(1,10,this).update(e,a),t.minFilter=o,a.geometry.dispose(),a.material.dispose(),this}clear(e,t=!0,n=!0,r=!0){let s=e.getRenderTarget();for(let a=0;a<6;a++)e.setRenderTarget(this,a),e.clear(t,n,r);e.setRenderTarget(s)}},Bt=class extends wt{constructor(){super(),this.isGroup=!0,this.type="Group"}},af={type:"move"},hr=class{constructor(){this._targetRay=null,this._grip=null,this._hand=null}getHandSpace(){return this._hand===null&&(this._hand=new Bt,this._hand.matrixAutoUpdate=!1,this._hand.visible=!1,this._hand.joints={},this._hand.inputState={pinching:!1}),this._hand}getTargetRaySpace(){return this._targetRay===null&&(this._targetRay=new Bt,this._targetRay.matrixAutoUpdate=!1,this._targetRay.visible=!1,this._targetRay.hasLinearVelocity=!1,this._targetRay.linearVelocity=new N,this._targetRay.hasAngularVelocity=!1,this._targetRay.angularVelocity=new N),this._targetRay}getGripSpace(){return this._grip===null&&(this._grip=new Bt,this._grip.matrixAutoUpdate=!1,this._grip.visible=!1,this._grip.hasLinearVelocity=!1,this._grip.linearVelocity=new N,this._grip.hasAngularVelocity=!1,this._grip.angularVelocity=new N),this._grip}dispatchEvent(e){return this._targetRay!==null&&this._targetRay.dispatchEvent(e),this._grip!==null&&this._grip.dispatchEvent(e),this._hand!==null&&this._hand.dispatchEvent(e),this}connect(e){if(e&&e.hand){let t=this._hand;if(t)for(let n of e.hand.values())this._getHandJoint(t,n)}return this.dispatchEvent({type:"connected",data:e}),this}disconnect(e){return this.dispatchEvent({type:"disconnected",data:e}),this._targetRay!==null&&(this._targetRay.visible=!1),this._grip!==null&&(this._grip.visible=!1),this._hand!==null&&(this._hand.visible=!1),this}update(e,t,n){let r=null,s=null,a=null,o=this._targetRay,l=this._grip,c=this._hand;if(e&&t.session.visibilityState!=="visible-blurred"){if(c&&e.hand){a=!0;for(let x of e.hand.values()){let m=t.getJointPose(x,n),f=this._getHandJoint(c,x);m!==null&&(f.matrix.fromArray(m.transform.matrix),f.matrix.decompose(f.position,f.rotation,f.scale),f.matrixWorldNeedsUpdate=!0,f.jointRadius=m.radius),f.visible=m!==null}let d=c.joints["index-finger-tip"],u=c.joints["thumb-tip"],h=d.position.distanceTo(u.position),p=.02,g=.005;c.inputState.pinching&&h>p+g?(c.inputState.pinching=!1,this.dispatchEvent({type:"pinchend",handedness:e.handedness,target:this})):!c.inputState.pinching&&h<=p-g&&(c.inputState.pinching=!0,this.dispatchEvent({type:"pinchstart",handedness:e.handedness,target:this}))}else l!==null&&e.gripSpace&&(s=t.getPose(e.gripSpace,n),s!==null&&(l.matrix.fromArray(s.transform.matrix),l.matrix.decompose(l.position,l.rotation,l.scale),l.matrixWorldNeedsUpdate=!0,s.linearVelocity?(l.hasLinearVelocity=!0,l.linearVelocity.copy(s.linearVelocity)):l.hasLinearVelocity=!1,s.angularVelocity?(l.hasAngularVelocity=!0,l.angularVelocity.copy(s.angularVelocity)):l.hasAngularVelocity=!1));o!==null&&(r=t.getPose(e.targetRaySpace,n),r===null&&s!==null&&(r=s),r!==null&&(o.matrix.fromArray(r.transform.matrix),o.matrix.decompose(o.position,o.rotation,o.scale),o.matrixWorldNeedsUpdate=!0,r.linearVelocity?(o.hasLinearVelocity=!0,o.linearVelocity.copy(r.linearVelocity)):o.hasLinearVelocity=!1,r.angularVelocity?(o.hasAngularVelocity=!0,o.angularVelocity.copy(r.angularVelocity)):o.hasAngularVelocity=!1,this.dispatchEvent(af)))}return o!==null&&(o.visible=r!==null),l!==null&&(l.visible=s!==null),c!==null&&(c.visible=a!==null),this}_getHandJoint(e,t){if(e.joints[t.jointName]===void 0){let n=new Bt;n.matrixAutoUpdate=!1,n.visible=!1,e.joints[t.jointName]=n,e.add(n)}return e.joints[t.jointName]}};var Zr=class extends wt{constructor(){super(),this.isScene=!0,this.type="Scene",this.background=null,this.environment=null,this.fog=null,this.backgroundBlurriness=0,this.backgroundIntensity=1,this.backgroundRotation=new en,this.environmentIntensity=1,this.environmentRotation=new en,this.overrideMaterial=null,typeof __THREE_DEVTOOLS__<"u"&&__THREE_DEVTOOLS__.dispatchEvent(new CustomEvent("observe",{detail:this}))}copy(e,t){return super.copy(e,t),e.background!==null&&(this.background=e.background.clone()),e.environment!==null&&(this.environment=e.environment.clone()),e.fog!==null&&(this.fog=e.fog.clone()),this.backgroundBlurriness=e.backgroundBlurriness,this.backgroundIntensity=e.backgroundIntensity,this.backgroundRotation.copy(e.backgroundRotation),this.environmentIntensity=e.environmentIntensity,this.environmentRotation.copy(e.environmentRotation),e.overrideMaterial!==null&&(this.overrideMaterial=e.overrideMaterial.clone()),this.matrixAutoUpdate=e.matrixAutoUpdate,this}toJSON(e){let t=super.toJSON(e);return this.fog!==null&&(t.object.fog=this.fog.toJSON()),this.backgroundBlurriness>0&&(t.object.backgroundBlurriness=this.backgroundBlurriness),this.backgroundIntensity!==1&&(t.object.backgroundIntensity=this.backgroundIntensity),t.object.backgroundRotation=this.backgroundRotation.toArray(),this.environmentIntensity!==1&&(t.object.environmentIntensity=this.environmentIntensity),t.object.environmentRotation=this.environmentRotation.toArray(),t}},xa=class{constructor(e,t){this.isInterleavedBuffer=!0,this.array=e,this.stride=t,this.count=e!==void 0?e.length/t:0,this.usage=ua,this.updateRanges=[],this.version=0,this.uuid=kn()}onUploadCallback(){}set needsUpdate(e){e===!0&&this.version++}setUsage(e){return this.usage=e,this}addUpdateRange(e,t){this.updateRanges.push({start:e,count:t})}clearUpdateRanges(){this.updateRanges.length=0}copy(e){return this.array=new e.array.constructor(e.array),this.count=e.count,this.stride=e.stride,this.usage=e.usage,this}copyAt(e,t,n){e*=this.stride,n*=t.stride;for(let r=0,s=this.stride;r<s;r++)this.array[e+r]=t.array[n+r];return this}set(e,t=0){return this.array.set(e,t),this}clone(e){e.arrayBuffers===void 0&&(e.arrayBuffers={}),this.array.buffer._uuid===void 0&&(this.array.buffer._uuid=kn()),e.arrayBuffers[this.array.buffer._uuid]===void 0&&(e.arrayBuffers[this.array.buffer._uuid]=this.array.slice(0).buffer);let t=new this.array.constructor(e.arrayBuffers[this.array.buffer._uuid]),n=new this.constructor(t,this.stride);return n.setUsage(this.usage),n}onUpload(e){return this.onUploadCallback=e,this}toJSON(e){return e.arrayBuffers===void 0&&(e.arrayBuffers={}),this.array.buffer._uuid===void 0&&(this.array.buffer._uuid=kn()),e.arrayBuffers[this.array.buffer._uuid]===void 0&&(e.arrayBuffers[this.array.buffer._uuid]=Array.from(new Uint32Array(this.array.buffer))),{uuid:this.uuid,buffer:this.array.buffer._uuid,type:this.array.constructor.name,stride:this.stride}}},Ot=new N,Jr=class i{constructor(e,t,n,r=!1){this.isInterleavedBufferAttribute=!0,this.name="",this.data=e,this.itemSize=t,this.offset=n,this.normalized=r}get count(){return this.data.count}get array(){return this.data.array}set needsUpdate(e){this.data.needsUpdate=e}applyMatrix4(e){for(let t=0,n=this.data.count;t<n;t++)Ot.fromBufferAttribute(this,t),Ot.applyMatrix4(e),this.setXYZ(t,Ot.x,Ot.y,Ot.z);return this}applyNormalMatrix(e){for(let t=0,n=this.count;t<n;t++)Ot.fromBufferAttribute(this,t),Ot.applyNormalMatrix(e),this.setXYZ(t,Ot.x,Ot.y,Ot.z);return this}transformDirection(e){for(let t=0,n=this.count;t<n;t++)Ot.fromBufferAttribute(this,t),Ot.transformDirection(e),this.setXYZ(t,Ot.x,Ot.y,Ot.z);return this}getComponent(e,t){let n=this.array[e*this.data.stride+this.offset+t];return this.normalized&&(n=_n(n,this.array)),n}setComponent(e,t,n){return this.normalized&&(n=Je(n,this.array)),this.data.array[e*this.data.stride+this.offset+t]=n,this}setX(e,t){return this.normalized&&(t=Je(t,this.array)),this.data.array[e*this.data.stride+this.offset]=t,this}setY(e,t){return this.normalized&&(t=Je(t,this.array)),this.data.array[e*this.data.stride+this.offset+1]=t,this}setZ(e,t){return this.normalized&&(t=Je(t,this.array)),this.data.array[e*this.data.stride+this.offset+2]=t,this}setW(e,t){return this.normalized&&(t=Je(t,this.array)),this.data.array[e*this.data.stride+this.offset+3]=t,this}getX(e){let t=this.data.array[e*this.data.stride+this.offset];return this.normalized&&(t=_n(t,this.array)),t}getY(e){let t=this.data.array[e*this.data.stride+this.offset+1];return this.normalized&&(t=_n(t,this.array)),t}getZ(e){let t=this.data.array[e*this.data.stride+this.offset+2];return this.normalized&&(t=_n(t,this.array)),t}getW(e){let t=this.data.array[e*this.data.stride+this.offset+3];return this.normalized&&(t=_n(t,this.array)),t}setXY(e,t,n){return e=e*this.data.stride+this.offset,this.normalized&&(t=Je(t,this.array),n=Je(n,this.array)),this.data.array[e+0]=t,this.data.array[e+1]=n,this}setXYZ(e,t,n,r){return e=e*this.data.stride+this.offset,this.normalized&&(t=Je(t,this.array),n=Je(n,this.array),r=Je(r,this.array)),this.data.array[e+0]=t,this.data.array[e+1]=n,this.data.array[e+2]=r,this}setXYZW(e,t,n,r,s){return e=e*this.data.stride+this.offset,this.normalized&&(t=Je(t,this.array),n=Je(n,this.array),r=Je(r,this.array),s=Je(s,this.array)),this.data.array[e+0]=t,this.data.array[e+1]=n,this.data.array[e+2]=r,this.data.array[e+3]=s,this}clone(e){if(e===void 0){console.log("THREE.InterleavedBufferAttribute.clone(): Cloning an interleaved buffer attribute will de-interleave buffer data.");let t=[];for(let n=0;n<this.count;n++){let r=n*this.data.stride+this.offset;for(let s=0;s<this.itemSize;s++)t.push(this.data.array[r+s])}return new Gt(new this.array.constructor(t),this.itemSize,this.normalized)}else return e.interleavedBuffers===void 0&&(e.interleavedBuffers={}),e.interleavedBuffers[this.data.uuid]===void 0&&(e.interleavedBuffers[this.data.uuid]=this.data.clone(e)),new i(e.interleavedBuffers[this.data.uuid],this.itemSize,this.offset,this.normalized)}toJSON(e){if(e===void 0){console.log("THREE.InterleavedBufferAttribute.toJSON(): Serializing an interleaved buffer attribute will de-interleave buffer data.");let t=[];for(let n=0;n<this.count;n++){let r=n*this.data.stride+this.offset;for(let s=0;s<this.itemSize;s++)t.push(this.data.array[r+s])}return{itemSize:this.itemSize,type:this.array.constructor.name,array:t,normalized:this.normalized}}else return e.interleavedBuffers===void 0&&(e.interleavedBuffers={}),e.interleavedBuffers[this.data.uuid]===void 0&&(e.interleavedBuffers[this.data.uuid]=this.data.toJSON(e)),{isInterleavedBufferAttribute:!0,itemSize:this.itemSize,data:this.data.uuid,offset:this.offset,normalized:this.normalized}}},fr=class extends bn{constructor(e){super(),this.isSpriteMaterial=!0,this.type="SpriteMaterial",this.color=new Ne(16777215),this.map=null,this.alphaMap=null,this.rotation=0,this.sizeAttenuation=!0,this.transparent=!0,this.fog=!0,this.setValues(e)}copy(e){return super.copy(e),this.color.copy(e.color),this.map=e.map,this.alphaMap=e.alphaMap,this.rotation=e.rotation,this.sizeAttenuation=e.sizeAttenuation,this.fog=e.fog,this}},tr,Lr=new N,nr=new N,ir=new N,rr=new He,Fr=new He,ru=new ct,$s=new N,Ur=new N,qs=new N,nd=new He,fl=new He,id=new He,Kr=class extends wt{constructor(e=new fr){if(super(),this.isSprite=!0,this.type="Sprite",tr===void 0){tr=new dt;let t=new Float32Array([-.5,-.5,0,0,0,.5,-.5,0,1,0,.5,.5,0,1,1,-.5,.5,0,0,1]),n=new xa(t,5);tr.setIndex([0,1,2,0,2,3]),tr.setAttribute("position",new Jr(n,3,0,!1)),tr.setAttribute("uv",new Jr(n,2,3,!1))}this.geometry=tr,this.material=e,this.center=new He(.5,.5),this.count=1}raycast(e,t){e.camera===null&&console.error('THREE.Sprite: "Raycaster.camera" needs to be set in order to raycast against sprites.'),nr.setFromMatrixScale(this.matrixWorld),ru.copy(e.camera.matrixWorld),this.modelViewMatrix.multiplyMatrices(e.camera.matrixWorldInverse,this.matrixWorld),ir.setFromMatrixPosition(this.modelViewMatrix),e.camera.isPerspectiveCamera&&this.material.sizeAttenuation===!1&&nr.multiplyScalar(-ir.z);let n=this.material.rotation,r,s;n!==0&&(s=Math.cos(n),r=Math.sin(n));let a=this.center;Ys($s.set(-.5,-.5,0),ir,a,nr,r,s),Ys(Ur.set(.5,-.5,0),ir,a,nr,r,s),Ys(qs.set(.5,.5,0),ir,a,nr,r,s),nd.set(0,0),fl.set(1,0),id.set(1,1);let o=e.ray.intersectTriangle($s,Ur,qs,!1,Lr);if(o===null&&(Ys(Ur.set(-.5,.5,0),ir,a,nr,r,s),fl.set(0,1),o=e.ray.intersectTriangle($s,qs,Ur,!1,Lr),o===null))return;let l=e.ray.origin.distanceTo(Lr);l<e.near||l>e.far||t.push({distance:l,point:Lr.clone(),uv:An.getInterpolation(Lr,$s,Ur,qs,nd,fl,id,new He),face:null,object:this})}copy(e,t){return super.copy(e,t),e.center!==void 0&&this.center.copy(e.center),this.material=e.material,this}};function Ys(i,e,t,n,r,s){rr.subVectors(i,t).addScalar(.5).multiply(n),r!==void 0?(Fr.x=s*rr.x-r*rr.y,Fr.y=r*rr.x+s*rr.y):Fr.copy(rr),i.copy(e),i.x+=Fr.x,i.y+=Fr.y,i.applyMatrix4(ru)}var pl=new N,of=new N,lf=new Oe,Tn=class{constructor(e=new N(1,0,0),t=0){this.isPlane=!0,this.normal=e,this.constant=t}set(e,t){return this.normal.copy(e),this.constant=t,this}setComponents(e,t,n,r){return this.normal.set(e,t,n),this.constant=r,this}setFromNormalAndCoplanarPoint(e,t){return this.normal.copy(e),this.constant=-t.dot(this.normal),this}setFromCoplanarPoints(e,t,n){let r=pl.subVectors(n,t).cross(of.subVectors(e,t)).normalize();return this.setFromNormalAndCoplanarPoint(r,e),this}copy(e){return this.normal.copy(e.normal),this.constant=e.constant,this}normalize(){let e=1/this.normal.length();return this.normal.multiplyScalar(e),this.constant*=e,this}negate(){return this.constant*=-1,this.normal.negate(),this}distanceToPoint(e){return this.normal.dot(e)+this.constant}distanceToSphere(e){return this.distanceToPoint(e.center)-e.radius}projectPoint(e,t){return t.copy(e).addScaledVector(this.normal,-this.distanceToPoint(e))}intersectLine(e,t){let n=e.delta(pl),r=this.normal.dot(n);if(r===0)return this.distanceToPoint(e.start)===0?t.copy(e.start):null;let s=-(e.start.dot(this.normal)+this.constant)/r;return s<0||s>1?null:t.copy(e.start).addScaledVector(n,s)}intersectsLine(e){let t=this.distanceToPoint(e.start),n=this.distanceToPoint(e.end);return t<0&&n>0||n<0&&t>0}intersectsBox(e){return e.intersectsPlane(this)}intersectsSphere(e){return e.intersectsPlane(this)}coplanarPoint(e){return e.copy(this.normal).multiplyScalar(-this.constant)}applyMatrix4(e,t){let n=t||lf.getNormalMatrix(e),r=this.coplanarPoint(pl).applyMatrix4(e),s=this.normal.applyMatrix3(n).normalize();return this.constant=-r.dot(s),this}translate(e){return this.constant-=e.dot(this.normal),this}equals(e){return e.normal.equals(this.normal)&&e.constant===this.constant}clone(){return new this.constructor().copy(this)}},vi=new ai,cf=new He(.5,.5),Zs=new N,pr=class{constructor(e=new Tn,t=new Tn,n=new Tn,r=new Tn,s=new Tn,a=new Tn){this.planes=[e,t,n,r,s,a]}set(e,t,n,r,s,a){let o=this.planes;return o[0].copy(e),o[1].copy(t),o[2].copy(n),o[3].copy(r),o[4].copy(s),o[5].copy(a),this}copy(e){let t=this.planes;for(let n=0;n<6;n++)t[n].copy(e.planes[n]);return this}setFromProjectionMatrix(e,t=yn,n=!1){let r=this.planes,s=e.elements,a=s[0],o=s[1],l=s[2],c=s[3],d=s[4],u=s[5],h=s[6],p=s[7],g=s[8],x=s[9],m=s[10],f=s[11],S=s[12],M=s[13],y=s[14],C=s[15];if(r[0].setComponents(c-a,p-d,f-g,C-S).normalize(),r[1].setComponents(c+a,p+d,f+g,C+S).normalize(),r[2].setComponents(c+o,p+u,f+x,C+M).normalize(),r[3].setComponents(c-o,p-u,f-x,C-M).normalize(),n)r[4].setComponents(l,h,m,y).normalize(),r[5].setComponents(c-l,p-h,f-m,C-y).normalize();else if(r[4].setComponents(c-l,p-h,f-m,C-y).normalize(),t===yn)r[5].setComponents(c+l,p+h,f+m,C+y).normalize();else if(t===Hr)r[5].setComponents(l,h,m,y).normalize();else throw new Error("THREE.Frustum.setFromProjectionMatrix(): Invalid coordinate system: "+t);return this}intersectsObject(e){if(e.boundingSphere!==void 0)e.boundingSphere===null&&e.computeBoundingSphere(),vi.copy(e.boundingSphere).applyMatrix4(e.matrixWorld);else{let t=e.geometry;t.boundingSphere===null&&t.computeBoundingSphere(),vi.copy(t.boundingSphere).applyMatrix4(e.matrixWorld)}return this.intersectsSphere(vi)}intersectsSprite(e){vi.center.set(0,0,0);let t=cf.distanceTo(e.center);return vi.radius=.7071067811865476+t,vi.applyMatrix4(e.matrixWorld),this.intersectsSphere(vi)}intersectsSphere(e){let t=this.planes,n=e.center,r=-e.radius;for(let s=0;s<6;s++)if(t[s].distanceToPoint(n)<r)return!1;return!0}intersectsBox(e){let t=this.planes;for(let n=0;n<6;n++){let r=t[n];if(Zs.x=r.normal.x>0?e.max.x:e.min.x,Zs.y=r.normal.y>0?e.max.y:e.min.y,Zs.z=r.normal.z>0?e.max.z:e.min.z,r.distanceToPoint(Zs)<0)return!1}return!0}containsPoint(e){let t=this.planes;for(let n=0;n<6;n++)if(t[n].distanceToPoint(e)<0)return!1;return!0}clone(){return new this.constructor().copy(this)}};var nn=class extends bn{constructor(e){super(),this.isLineBasicMaterial=!0,this.type="LineBasicMaterial",this.color=new Ne(16777215),this.map=null,this.linewidth=1,this.linecap="round",this.linejoin="round",this.fog=!0,this.setValues(e)}copy(e){return super.copy(e),this.color.copy(e.color),this.map=e.map,this.linewidth=e.linewidth,this.linecap=e.linecap,this.linejoin=e.linejoin,this.fog=e.fog,this}},_a=new N,ya=new N,rd=new ct,Or=new ur,Js=new ai,ml=new N,sd=new N,Wn=class extends wt{constructor(e=new dt,t=new nn){super(),this.isLine=!0,this.type="Line",this.geometry=e,this.material=t,this.morphTargetDictionary=void 0,this.morphTargetInfluences=void 0,this.updateMorphTargets()}copy(e,t){return super.copy(e,t),this.material=Array.isArray(e.material)?e.material.slice():e.material,this.geometry=e.geometry,this}computeLineDistances(){let e=this.geometry;if(e.index===null){let t=e.attributes.position,n=[0];for(let r=1,s=t.count;r<s;r++)_a.fromBufferAttribute(t,r-1),ya.fromBufferAttribute(t,r),n[r]=n[r-1],n[r]+=_a.distanceTo(ya);e.setAttribute("lineDistance",new je(n,1))}else console.warn("THREE.Line.computeLineDistances(): Computation only possible with non-indexed BufferGeometry.");return this}raycast(e,t){let n=this.geometry,r=this.matrixWorld,s=e.params.Line.threshold,a=n.drawRange;if(n.boundingSphere===null&&n.computeBoundingSphere(),Js.copy(n.boundingSphere),Js.applyMatrix4(r),Js.radius+=s,e.ray.intersectsSphere(Js)===!1)return;rd.copy(r).invert(),Or.copy(e.ray).applyMatrix4(rd);let o=s/((this.scale.x+this.scale.y+this.scale.z)/3),l=o*o,c=this.isLineSegments?2:1,d=n.index,h=n.attributes.position;if(d!==null){let p=Math.max(0,a.start),g=Math.min(d.count,a.start+a.count);for(let x=p,m=g-1;x<m;x+=c){let f=d.getX(x),S=d.getX(x+1),M=Ks(this,e,Or,l,f,S,x);M&&t.push(M)}if(this.isLineLoop){let x=d.getX(g-1),m=d.getX(p),f=Ks(this,e,Or,l,x,m,g-1);f&&t.push(f)}}else{let p=Math.max(0,a.start),g=Math.min(h.count,a.start+a.count);for(let x=p,m=g-1;x<m;x+=c){let f=Ks(this,e,Or,l,x,x+1,x);f&&t.push(f)}if(this.isLineLoop){let x=Ks(this,e,Or,l,g-1,p,g-1);x&&t.push(x)}}}updateMorphTargets(){let t=this.geometry.morphAttributes,n=Object.keys(t);if(n.length>0){let r=t[n[0]];if(r!==void 0){this.morphTargetInfluences=[],this.morphTargetDictionary={};for(let s=0,a=r.length;s<a;s++){let o=r[s].name||String(s);this.morphTargetInfluences.push(0),this.morphTargetDictionary[o]=s}}}}};function Ks(i,e,t,n,r,s,a){let o=i.geometry.attributes.position;if(_a.fromBufferAttribute(o,r),ya.fromBufferAttribute(o,s),t.distanceSqToSegment(_a,ya,ml,sd)>n)return;ml.applyMatrix4(i.matrixWorld);let c=e.ray.origin.distanceTo(ml);if(!(c<e.near||c>e.far))return{distance:c,point:sd.clone().applyMatrix4(i.matrixWorld),index:a,face:null,faceIndex:null,barycoord:null,object:i}}var ad=new N,od=new N,oi=class extends Wn{constructor(e,t){super(e,t),this.isLineSegments=!0,this.type="LineSegments"}computeLineDistances(){let e=this.geometry;if(e.index===null){let t=e.attributes.position,n=[];for(let r=0,s=t.count;r<s;r+=2)ad.fromBufferAttribute(t,r),od.fromBufferAttribute(t,r+1),n[r]=r===0?0:n[r-1],n[r+1]=n[r]+ad.distanceTo(od);e.setAttribute("lineDistance",new je(n,1))}else console.warn("THREE.LineSegments.computeLineDistances(): Computation only possible with non-indexed BufferGeometry.");return this}};var va=class extends bn{constructor(e){super(),this.isPointsMaterial=!0,this.type="PointsMaterial",this.color=new Ne(16777215),this.map=null,this.alphaMap=null,this.size=1,this.sizeAttenuation=!0,this.fog=!0,this.setValues(e)}copy(e){return super.copy(e),this.color.copy(e.color),this.map=e.map,this.alphaMap=e.alphaMap,this.size=e.size,this.sizeAttenuation=e.sizeAttenuation,this.fog=e.fog,this}},ld=new ct,Ml=new ur,js=new ai,Qs=new N,jr=class extends wt{constructor(e=new dt,t=new va){super(),this.isPoints=!0,this.type="Points",this.geometry=e,this.material=t,this.morphTargetDictionary=void 0,this.morphTargetInfluences=void 0,this.updateMorphTargets()}copy(e,t){return super.copy(e,t),this.material=Array.isArray(e.material)?e.material.slice():e.material,this.geometry=e.geometry,this}raycast(e,t){let n=this.geometry,r=this.matrixWorld,s=e.params.Points.threshold,a=n.drawRange;if(n.boundingSphere===null&&n.computeBoundingSphere(),js.copy(n.boundingSphere),js.applyMatrix4(r),js.radius+=s,e.ray.intersectsSphere(js)===!1)return;ld.copy(r).invert(),Ml.copy(e.ray).applyMatrix4(ld);let o=s/((this.scale.x+this.scale.y+this.scale.z)/3),l=o*o,c=n.index,u=n.attributes.position;if(c!==null){let h=Math.max(0,a.start),p=Math.min(c.count,a.start+a.count);for(let g=h,x=p;g<x;g++){let m=c.getX(g);Qs.fromBufferAttribute(u,m),cd(Qs,m,l,r,e,t,this)}}else{let h=Math.max(0,a.start),p=Math.min(u.count,a.start+a.count);for(let g=h,x=p;g<x;g++)Qs.fromBufferAttribute(u,g),cd(Qs,g,l,r,e,t,this)}}updateMorphTargets(){let t=this.geometry.morphAttributes,n=Object.keys(t);if(n.length>0){let r=t[n[0]];if(r!==void 0){this.morphTargetInfluences=[],this.morphTargetDictionary={};for(let s=0,a=r.length;s<a;s++){let o=r[s].name||String(s);this.morphTargetInfluences.push(0),this.morphTargetDictionary[o]=s}}}}};function cd(i,e,t,n,r,s,a){let o=Ml.distanceSqToPoint(i);if(o<t){let l=new N;Ml.closestPointToPoint(i,l),l.applyMatrix4(n);let c=r.ray.origin.distanceTo(l);if(c<r.near||c>r.far)return;s.push({distance:c,distanceToRay:Math.sqrt(o),point:l,index:e,face:null,faceIndex:null,barycoord:null,object:a})}}var Qr=class extends Lt{constructor(e,t,n,r,s,a,o,l,c){super(e,t,n,r,s,a,o,l,c),this.isCanvasTexture=!0,this.needsUpdate=!0}},es=class extends Lt{constructor(e,t,n=hi,r,s,a,o=cn,l=cn,c,d=or,u=1){if(d!==or&&d!==yr)throw new Error("DepthTexture format must be either THREE.DepthFormat or THREE.DepthStencilFormat");let h={width:e,height:t,depth:u};super(h,r,s,a,o,l,d,n,c),this.isDepthTexture=!0,this.flipY=!1,this.generateMipmaps=!1,this.compareFunction=null}copy(e){return super.copy(e),this.source=new dr(Object.assign({},e.image)),this.compareFunction=e.compareFunction,this}toJSON(e){let t=super.toJSON(e);return this.compareFunction!==null&&(t.compareFunction=this.compareFunction),t}},ts=class extends Lt{constructor(e=null){super(),this.sourceTexture=e,this.isExternalTexture=!0}copy(e){return super.copy(e),this.sourceTexture=e.sourceTexture,this}};var Rn=class i extends dt{constructor(e=1,t=1,n=1,r=32,s=1,a=!1,o=0,l=Math.PI*2){super(),this.type="CylinderGeometry",this.parameters={radiusTop:e,radiusBottom:t,height:n,radialSegments:r,heightSegments:s,openEnded:a,thetaStart:o,thetaLength:l};let c=this;r=Math.floor(r),s=Math.floor(s);let d=[],u=[],h=[],p=[],g=0,x=[],m=n/2,f=0;S(),a===!1&&(e>0&&M(!0),t>0&&M(!1)),this.setIndex(d),this.setAttribute("position",new je(u,3)),this.setAttribute("normal",new je(h,3)),this.setAttribute("uv",new je(p,2));function S(){let y=new N,C=new N,E=0,R=(t-e)/n;for(let P=0;P<=s;P++){let w=[],v=P/s,T=v*(t-e)+e;for(let D=0;D<=r;D++){let F=D/r,B=F*l+o,k=Math.sin(B),W=Math.cos(B);C.x=T*k,C.y=-v*n+m,C.z=T*W,u.push(C.x,C.y,C.z),y.set(k,R,W).normalize(),h.push(y.x,y.y,y.z),p.push(F,1-v),w.push(g++)}x.push(w)}for(let P=0;P<r;P++)for(let w=0;w<s;w++){let v=x[w][P],T=x[w+1][P],D=x[w+1][P+1],F=x[w][P+1];(e>0||w!==0)&&(d.push(v,T,F),E+=3),(t>0||w!==s-1)&&(d.push(T,D,F),E+=3)}c.addGroup(f,E,0),f+=E}function M(y){let C=g,E=new He,R=new N,P=0,w=y===!0?e:t,v=y===!0?1:-1;for(let D=1;D<=r;D++)u.push(0,m*v,0),h.push(0,v,0),p.push(.5,.5),g++;let T=g;for(let D=0;D<=r;D++){let B=D/r*l+o,k=Math.cos(B),W=Math.sin(B);R.x=w*W,R.y=m*v,R.z=w*k,u.push(R.x,R.y,R.z),h.push(0,v,0),E.x=k*.5+.5,E.y=W*.5*v+.5,p.push(E.x,E.y),g++}for(let D=0;D<r;D++){let F=C+D,B=T+D;y===!0?d.push(B,B+1,F):d.push(B+1,B,F),P+=3}c.addGroup(f,P,y===!0?1:2),f+=P}}copy(e){return super.copy(e),this.parameters=Object.assign({},e.parameters),this}static fromJSON(e){return new i(e.radiusTop,e.radiusBottom,e.height,e.radialSegments,e.heightSegments,e.openEnded,e.thetaStart,e.thetaLength)}},mr=class i extends Rn{constructor(e=1,t=1,n=32,r=1,s=!1,a=0,o=Math.PI*2){super(0,e,t,n,r,s,a,o),this.type="ConeGeometry",this.parameters={radius:e,height:t,radialSegments:n,heightSegments:r,openEnded:s,thetaStart:a,thetaLength:o}}static fromJSON(e){return new i(e.radius,e.height,e.radialSegments,e.heightSegments,e.openEnded,e.thetaStart,e.thetaLength)}};var ea=new N,ta=new N,gl=new N,na=new An,ns=class extends dt{constructor(e=null,t=1){if(super(),this.type="EdgesGeometry",this.parameters={geometry:e,thresholdAngle:t},e!==null){let r=Math.pow(10,4),s=Math.cos(sr*t),a=e.getIndex(),o=e.getAttribute("position"),l=a?a.count:o.count,c=[0,0,0],d=["a","b","c"],u=new Array(3),h={},p=[];for(let g=0;g<l;g+=3){a?(c[0]=a.getX(g),c[1]=a.getX(g+1),c[2]=a.getX(g+2)):(c[0]=g,c[1]=g+1,c[2]=g+2);let{a:x,b:m,c:f}=na;if(x.fromBufferAttribute(o,c[0]),m.fromBufferAttribute(o,c[1]),f.fromBufferAttribute(o,c[2]),na.getNormal(gl),u[0]=`${Math.round(x.x*r)},${Math.round(x.y*r)},${Math.round(x.z*r)}`,u[1]=`${Math.round(m.x*r)},${Math.round(m.y*r)},${Math.round(m.z*r)}`,u[2]=`${Math.round(f.x*r)},${Math.round(f.y*r)},${Math.round(f.z*r)}`,!(u[0]===u[1]||u[1]===u[2]||u[2]===u[0]))for(let S=0;S<3;S++){let M=(S+1)%3,y=u[S],C=u[M],E=na[d[S]],R=na[d[M]],P=`${y}_${C}`,w=`${C}_${y}`;w in h&&h[w]?(gl.dot(h[w].normal)<=s&&(p.push(E.x,E.y,E.z),p.push(R.x,R.y,R.z)),h[w]=null):P in h||(h[P]={index0:c[S],index1:c[M],normal:gl.clone()})}}for(let g in h)if(h[g]){let{index0:x,index1:m}=h[g];ea.fromBufferAttribute(o,x),ta.fromBufferAttribute(o,m),p.push(ea.x,ea.y,ea.z),p.push(ta.x,ta.y,ta.z)}this.setAttribute("position",new je(p,3))}}copy(e){return super.copy(e),this.parameters=Object.assign({},e.parameters),this}};var Ei=class i extends dt{constructor(e=1,t=1,n=1,r=1){super(),this.type="PlaneGeometry",this.parameters={width:e,height:t,widthSegments:n,heightSegments:r};let s=e/2,a=t/2,o=Math.floor(n),l=Math.floor(r),c=o+1,d=l+1,u=e/o,h=t/l,p=[],g=[],x=[],m=[];for(let f=0;f<d;f++){let S=f*h-a;for(let M=0;M<c;M++){let y=M*u-s;g.push(y,-S,0),x.push(0,0,1),m.push(M/o),m.push(1-f/l)}}for(let f=0;f<l;f++)for(let S=0;S<o;S++){let M=S+c*f,y=S+c*(f+1),C=S+1+c*(f+1),E=S+1+c*f;p.push(M,y,E),p.push(y,C,E)}this.setIndex(p),this.setAttribute("position",new je(g,3)),this.setAttribute("normal",new je(x,3)),this.setAttribute("uv",new je(m,2))}copy(e){return super.copy(e),this.parameters=Object.assign({},e.parameters),this}static fromJSON(e){return new i(e.width,e.height,e.widthSegments,e.heightSegments)}};var li=class i extends dt{constructor(e=1,t=32,n=16,r=0,s=Math.PI*2,a=0,o=Math.PI){super(),this.type="SphereGeometry",this.parameters={radius:e,widthSegments:t,heightSegments:n,phiStart:r,phiLength:s,thetaStart:a,thetaLength:o},t=Math.max(3,Math.floor(t)),n=Math.max(2,Math.floor(n));let l=Math.min(a+o,Math.PI),c=0,d=[],u=new N,h=new N,p=[],g=[],x=[],m=[];for(let f=0;f<=n;f++){let S=[],M=f/n,y=0;f===0&&a===0?y=.5/t:f===n&&l===Math.PI&&(y=-.5/t);for(let C=0;C<=t;C++){let E=C/t;u.x=-e*Math.cos(r+E*s)*Math.sin(a+M*o),u.y=e*Math.cos(a+M*o),u.z=e*Math.sin(r+E*s)*Math.sin(a+M*o),g.push(u.x,u.y,u.z),h.copy(u).normalize(),x.push(h.x,h.y,h.z),m.push(E+y,1-M),S.push(c++)}d.push(S)}for(let f=0;f<n;f++)for(let S=0;S<t;S++){let M=d[f][S+1],y=d[f][S],C=d[f+1][S],E=d[f+1][S+1];(f!==0||a>0)&&p.push(M,y,E),(f!==n-1||l<Math.PI)&&p.push(y,C,E)}this.setIndex(p),this.setAttribute("position",new je(g,3)),this.setAttribute("normal",new je(x,3)),this.setAttribute("uv",new je(m,2))}copy(e){return super.copy(e),this.parameters=Object.assign({},e.parameters),this}static fromJSON(e){return new i(e.radius,e.widthSegments,e.heightSegments,e.phiStart,e.phiLength,e.thetaStart,e.thetaLength)}};var is=class extends bn{constructor(e){super(),this.isMeshStandardMaterial=!0,this.type="MeshStandardMaterial",this.defines={STANDARD:""},this.color=new Ne(16777215),this.roughness=1,this.metalness=0,this.map=null,this.lightMap=null,this.lightMapIntensity=1,this.aoMap=null,this.aoMapIntensity=1,this.emissive=new Ne(0),this.emissiveIntensity=1,this.emissiveMap=null,this.bumpMap=null,this.bumpScale=1,this.normalMap=null,this.normalMapType=Vl,this.normalScale=new He(1,1),this.displacementMap=null,this.displacementScale=1,this.displacementBias=0,this.roughnessMap=null,this.metalnessMap=null,this.alphaMap=null,this.envMap=null,this.envMapRotation=new en,this.envMapIntensity=1,this.wireframe=!1,this.wireframeLinewidth=1,this.wireframeLinecap="round",this.wireframeLinejoin="round",this.flatShading=!1,this.fog=!0,this.setValues(e)}copy(e){return super.copy(e),this.defines={STANDARD:""},this.color.copy(e.color),this.roughness=e.roughness,this.metalness=e.metalness,this.map=e.map,this.lightMap=e.lightMap,this.lightMapIntensity=e.lightMapIntensity,this.aoMap=e.aoMap,this.aoMapIntensity=e.aoMapIntensity,this.emissive.copy(e.emissive),this.emissiveMap=e.emissiveMap,this.emissiveIntensity=e.emissiveIntensity,this.bumpMap=e.bumpMap,this.bumpScale=e.bumpScale,this.normalMap=e.normalMap,this.normalMapType=e.normalMapType,this.normalScale.copy(e.normalScale),this.displacementMap=e.displacementMap,this.displacementScale=e.displacementScale,this.displacementBias=e.displacementBias,this.roughnessMap=e.roughnessMap,this.metalnessMap=e.metalnessMap,this.alphaMap=e.alphaMap,this.envMap=e.envMap,this.envMapRotation.copy(e.envMapRotation),this.envMapIntensity=e.envMapIntensity,this.wireframe=e.wireframe,this.wireframeLinewidth=e.wireframeLinewidth,this.wireframeLinecap=e.wireframeLinecap,this.wireframeLinejoin=e.wireframeLinejoin,this.flatShading=e.flatShading,this.fog=e.fog,this}};var ba=class extends bn{constructor(e){super(),this.isMeshDepthMaterial=!0,this.type="MeshDepthMaterial",this.depthPacking=Wd,this.map=null,this.alphaMap=null,this.displacementMap=null,this.displacementScale=1,this.displacementBias=0,this.wireframe=!1,this.wireframeLinewidth=1,this.setValues(e)}copy(e){return super.copy(e),this.depthPacking=e.depthPacking,this.map=e.map,this.alphaMap=e.alphaMap,this.displacementMap=e.displacementMap,this.displacementScale=e.displacementScale,this.displacementBias=e.displacementBias,this.wireframe=e.wireframe,this.wireframeLinewidth=e.wireframeLinewidth,this}},wa=class extends bn{constructor(e){super(),this.isMeshDistanceMaterial=!0,this.type="MeshDistanceMaterial",this.map=null,this.alphaMap=null,this.displacementMap=null,this.displacementScale=1,this.displacementBias=0,this.setValues(e)}copy(e){return super.copy(e),this.map=e.map,this.alphaMap=e.alphaMap,this.displacementMap=e.displacementMap,this.displacementScale=e.displacementScale,this.displacementBias=e.displacementBias,this}};function ia(i,e){return!i||i.constructor===e?i:typeof e.BYTES_PER_ELEMENT=="number"?new e(i):Array.prototype.slice.call(i)}function df(i){return ArrayBuffer.isView(i)&&!(i instanceof DataView)}var Ti=class{constructor(e,t,n,r){this.parameterPositions=e,this._cachedIndex=0,this.resultBuffer=r!==void 0?r:new t.constructor(n),this.sampleValues=t,this.valueSize=n,this.settings=null,this.DefaultSettings_={}}evaluate(e){let t=this.parameterPositions,n=this._cachedIndex,r=t[n],s=t[n-1];n:{e:{let a;t:{i:if(!(e<r)){for(let o=n+2;;){if(r===void 0){if(e<s)break i;return n=t.length,this._cachedIndex=n,this.copySampleValue_(n-1)}if(n===o)break;if(s=r,r=t[++n],e<r)break e}a=t.length;break t}if(!(e>=s)){let o=t[1];e<o&&(n=2,s=o);for(let l=n-2;;){if(s===void 0)return this._cachedIndex=0,this.copySampleValue_(0);if(n===l)break;if(r=s,s=t[--n-1],e>=s)break e}a=n,n=0;break t}break n}for(;n<a;){let o=n+a>>>1;e<t[o]?a=o:n=o+1}if(r=t[n],s=t[n-1],s===void 0)return this._cachedIndex=0,this.copySampleValue_(0);if(r===void 0)return n=t.length,this._cachedIndex=n,this.copySampleValue_(n-1)}this._cachedIndex=n,this.intervalChanged_(n,s,r)}return this.interpolate_(n,s,e,r)}getSettings_(){return this.settings||this.DefaultSettings_}copySampleValue_(e){let t=this.resultBuffer,n=this.sampleValues,r=this.valueSize,s=e*r;for(let a=0;a!==r;++a)t[a]=n[s+a];return t}interpolate_(){throw new Error("call to abstract method")}intervalChanged_(){}},Ma=class extends Ti{constructor(e,t,n,r){super(e,t,n,r),this._weightPrev=-0,this._offsetPrev=-0,this._weightNext=-0,this._offsetNext=-0,this.DefaultSettings_={endingStart:yl,endingEnd:yl}}intervalChanged_(e,t,n){let r=this.parameterPositions,s=e-2,a=e+1,o=r[s],l=r[a];if(o===void 0)switch(this.getSettings_().endingStart){case vl:s=e,o=2*t-n;break;case bl:s=r.length-2,o=t+r[s]-r[s+1];break;default:s=e,o=n}if(l===void 0)switch(this.getSettings_().endingEnd){case vl:a=e,l=2*n-t;break;case bl:a=1,l=n+r[1]-r[0];break;default:a=e-1,l=t}let c=(n-t)*.5,d=this.valueSize;this._weightPrev=c/(t-o),this._weightNext=c/(l-n),this._offsetPrev=s*d,this._offsetNext=a*d}interpolate_(e,t,n,r){let s=this.resultBuffer,a=this.sampleValues,o=this.valueSize,l=e*o,c=l-o,d=this._offsetPrev,u=this._offsetNext,h=this._weightPrev,p=this._weightNext,g=(n-t)/(r-t),x=g*g,m=x*g,f=-h*m+2*h*x-h*g,S=(1+h)*m+(-1.5-2*h)*x+(-.5+h)*g+1,M=(-1-p)*m+(1.5+p)*x+.5*g,y=p*m-p*x;for(let C=0;C!==o;++C)s[C]=f*a[d+C]+S*a[c+C]+M*a[l+C]+y*a[u+C];return s}},Sa=class extends Ti{constructor(e,t,n,r){super(e,t,n,r)}interpolate_(e,t,n,r){let s=this.resultBuffer,a=this.sampleValues,o=this.valueSize,l=e*o,c=l-o,d=(n-t)/(r-t),u=1-d;for(let h=0;h!==o;++h)s[h]=a[c+h]*u+a[l+h]*d;return s}},Ea=class extends Ti{constructor(e,t,n,r){super(e,t,n,r)}interpolate_(e){return this.copySampleValue_(e-1)}},rn=class{constructor(e,t,n,r){if(e===void 0)throw new Error("THREE.KeyframeTrack: track name is undefined");if(t===void 0||t.length===0)throw new Error("THREE.KeyframeTrack: no keyframes in track named "+e);this.name=e,this.times=ia(t,this.TimeBufferType),this.values=ia(n,this.ValueBufferType),this.setInterpolation(r||this.DefaultInterpolation)}static toJSON(e){let t=e.constructor,n;if(t.toJSON!==this.toJSON)n=t.toJSON(e);else{n={name:e.name,times:ia(e.times,Array),values:ia(e.values,Array)};let r=e.getInterpolation();r!==e.DefaultInterpolation&&(n.interpolation=r)}return n.type=e.ValueTypeName,n}InterpolantFactoryMethodDiscrete(e){return new Ea(this.times,this.values,this.getValueSize(),e)}InterpolantFactoryMethodLinear(e){return new Sa(this.times,this.values,this.getValueSize(),e)}InterpolantFactoryMethodSmooth(e){return new Ma(this.times,this.values,this.getValueSize(),e)}setInterpolation(e){let t;switch(e){case zr:t=this.InterpolantFactoryMethodDiscrete;break;case da:t=this.InterpolantFactoryMethodLinear;break;case sa:t=this.InterpolantFactoryMethodSmooth;break}if(t===void 0){let n="unsupported interpolation for "+this.ValueTypeName+" keyframe track named "+this.name;if(this.createInterpolant===void 0)if(e!==this.DefaultInterpolation)this.setInterpolation(this.DefaultInterpolation);else throw new Error(n);return console.warn("THREE.KeyframeTrack:",n),this}return this.createInterpolant=t,this}getInterpolation(){switch(this.createInterpolant){case this.InterpolantFactoryMethodDiscrete:return zr;case this.InterpolantFactoryMethodLinear:return da;case this.InterpolantFactoryMethodSmooth:return sa}}getValueSize(){return this.values.length/this.times.length}shift(e){if(e!==0){let t=this.times;for(let n=0,r=t.length;n!==r;++n)t[n]+=e}return this}scale(e){if(e!==1){let t=this.times;for(let n=0,r=t.length;n!==r;++n)t[n]*=e}return this}trim(e,t){let n=this.times,r=n.length,s=0,a=r-1;for(;s!==r&&n[s]<e;)++s;for(;a!==-1&&n[a]>t;)--a;if(++a,s!==0||a!==r){s>=a&&(a=Math.max(a,1),s=a-1);let o=this.getValueSize();this.times=n.slice(s,a),this.values=this.values.slice(s*o,a*o)}return this}validate(){let e=!0,t=this.getValueSize();t-Math.floor(t)!==0&&(console.error("THREE.KeyframeTrack: Invalid value size in track.",this),e=!1);let n=this.times,r=this.values,s=n.length;s===0&&(console.error("THREE.KeyframeTrack: Track is empty.",this),e=!1);let a=null;for(let o=0;o!==s;o++){let l=n[o];if(typeof l=="number"&&isNaN(l)){console.error("THREE.KeyframeTrack: Time is not a valid number.",this,o,l),e=!1;break}if(a!==null&&a>l){console.error("THREE.KeyframeTrack: Out of order keys.",this,o,l,a),e=!1;break}a=l}if(r!==void 0&&df(r))for(let o=0,l=r.length;o!==l;++o){let c=r[o];if(isNaN(c)){console.error("THREE.KeyframeTrack: Value is not a valid number.",this,o,c),e=!1;break}}return e}optimize(){let e=this.times.slice(),t=this.values.slice(),n=this.getValueSize(),r=this.getInterpolation()===sa,s=e.length-1,a=1;for(let o=1;o<s;++o){let l=!1,c=e[o],d=e[o+1];if(c!==d&&(o!==1||c!==e[0]))if(r)l=!0;else{let u=o*n,h=u-n,p=u+n;for(let g=0;g!==n;++g){let x=t[u+g];if(x!==t[h+g]||x!==t[p+g]){l=!0;break}}}if(l){if(o!==a){e[a]=e[o];let u=o*n,h=a*n;for(let p=0;p!==n;++p)t[h+p]=t[u+p]}++a}}if(s>0){e[a]=e[s];for(let o=s*n,l=a*n,c=0;c!==n;++c)t[l+c]=t[o+c];++a}return a!==e.length?(this.times=e.slice(0,a),this.values=t.slice(0,a*n)):(this.times=e,this.values=t),this}clone(){let e=this.times.slice(),t=this.values.slice(),n=this.constructor,r=new n(this.name,e,t);return r.createInterpolant=this.createInterpolant,r}};rn.prototype.ValueTypeName="";rn.prototype.TimeBufferType=Float32Array;rn.prototype.ValueBufferType=Float32Array;rn.prototype.DefaultInterpolation=da;var ci=class extends rn{constructor(e,t,n){super(e,t,n)}};ci.prototype.ValueTypeName="bool";ci.prototype.ValueBufferType=Array;ci.prototype.DefaultInterpolation=zr;ci.prototype.InterpolantFactoryMethodLinear=void 0;ci.prototype.InterpolantFactoryMethodSmooth=void 0;var Ta=class extends rn{constructor(e,t,n,r){super(e,t,n,r)}};Ta.prototype.ValueTypeName="color";var Aa=class extends rn{constructor(e,t,n,r){super(e,t,n,r)}};Aa.prototype.ValueTypeName="number";var Ca=class extends Ti{constructor(e,t,n,r){super(e,t,n,r)}interpolate_(e,t,n,r){let s=this.resultBuffer,a=this.sampleValues,o=this.valueSize,l=(n-t)/(r-t),c=e*o;for(let d=c+o;c!==d;c+=4)Wt.slerpFlat(s,0,a,c-o,a,c,l);return s}},rs=class extends rn{constructor(e,t,n,r){super(e,t,n,r)}InterpolantFactoryMethodLinear(e){return new Ca(this.times,this.values,this.getValueSize(),e)}};rs.prototype.ValueTypeName="quaternion";rs.prototype.InterpolantFactoryMethodSmooth=void 0;var di=class extends rn{constructor(e,t,n){super(e,t,n)}};di.prototype.ValueTypeName="string";di.prototype.ValueBufferType=Array;di.prototype.DefaultInterpolation=zr;di.prototype.InterpolantFactoryMethodLinear=void 0;di.prototype.InterpolantFactoryMethodSmooth=void 0;var Ra=class extends rn{constructor(e,t,n,r){super(e,t,n,r)}};Ra.prototype.ValueTypeName="vector";var Ia=class{constructor(e,t,n){let r=this,s=!1,a=0,o=0,l,c=[];this.onStart=void 0,this.onLoad=e,this.onProgress=t,this.onError=n,this.abortController=new AbortController,this.itemStart=function(d){o++,s===!1&&r.onStart!==void 0&&r.onStart(d,a,o),s=!0},this.itemEnd=function(d){a++,r.onProgress!==void 0&&r.onProgress(d,a,o),a===o&&(s=!1,r.onLoad!==void 0&&r.onLoad())},this.itemError=function(d){r.onError!==void 0&&r.onError(d)},this.resolveURL=function(d){return l?l(d):d},this.setURLModifier=function(d){return l=d,this},this.addHandler=function(d,u){return c.push(d,u),this},this.removeHandler=function(d){let u=c.indexOf(d);return u!==-1&&c.splice(u,2),this},this.getHandler=function(d){for(let u=0,h=c.length;u<h;u+=2){let p=c[u],g=c[u+1];if(p.global&&(p.lastIndex=0),p.test(d))return g}return null},this.abort=function(){return this.abortController.abort(),this.abortController=new AbortController,this}}},su=new Ia,Pa=class{constructor(e){this.manager=e!==void 0?e:su,this.crossOrigin="anonymous",this.withCredentials=!1,this.path="",this.resourcePath="",this.requestHeader={}}load(){}loadAsync(e,t){let n=this;return new Promise(function(r,s){n.load(e,r,t,s)})}parse(){}setCrossOrigin(e){return this.crossOrigin=e,this}setWithCredentials(e){return this.withCredentials=e,this}setPath(e){return this.path=e,this}setResourcePath(e){return this.resourcePath=e,this}setRequestHeader(e){return this.requestHeader=e,this}abort(){return this}};Pa.DEFAULT_MATERIAL_NAME="__DEFAULT";var ss=class extends wt{constructor(e,t=1){super(),this.isLight=!0,this.type="Light",this.color=new Ne(e),this.intensity=t}dispose(){}copy(e,t){return super.copy(e,t),this.color.copy(e.color),this.intensity=e.intensity,this}toJSON(e){let t=super.toJSON(e);return t.object.color=this.color.getHex(),t.object.intensity=this.intensity,this.groundColor!==void 0&&(t.object.groundColor=this.groundColor.getHex()),this.distance!==void 0&&(t.object.distance=this.distance),this.angle!==void 0&&(t.object.angle=this.angle),this.decay!==void 0&&(t.object.decay=this.decay),this.penumbra!==void 0&&(t.object.penumbra=this.penumbra),this.shadow!==void 0&&(t.object.shadow=this.shadow.toJSON()),this.target!==void 0&&(t.object.target=this.target.uuid),t}},as=class extends ss{constructor(e,t,n){super(e,n),this.isHemisphereLight=!0,this.type="HemisphereLight",this.position.copy(wt.DEFAULT_UP),this.updateMatrix(),this.groundColor=new Ne(t)}copy(e,t){return super.copy(e,t),this.groundColor.copy(e.groundColor),this}},xl=new ct,dd=new N,ud=new N,Sl=class{constructor(e){this.camera=e,this.intensity=1,this.bias=0,this.normalBias=0,this.radius=1,this.blurSamples=8,this.mapSize=new He(512,512),this.mapType=Mn,this.map=null,this.mapPass=null,this.matrix=new ct,this.autoUpdate=!0,this.needsUpdate=!1,this._frustum=new pr,this._frameExtents=new He(1,1),this._viewportCount=1,this._viewports=[new pt(0,0,1,1)]}getViewportCount(){return this._viewportCount}getFrustum(){return this._frustum}updateMatrices(e){let t=this.camera,n=this.matrix;dd.setFromMatrixPosition(e.matrixWorld),t.position.copy(dd),ud.setFromMatrixPosition(e.target.matrixWorld),t.lookAt(ud),t.updateMatrixWorld(),xl.multiplyMatrices(t.projectionMatrix,t.matrixWorldInverse),this._frustum.setFromProjectionMatrix(xl,t.coordinateSystem,t.reversedDepth),t.reversedDepth?n.set(.5,0,0,.5,0,.5,0,.5,0,0,1,0,0,0,0,1):n.set(.5,0,0,.5,0,.5,0,.5,0,0,.5,.5,0,0,0,1),n.multiply(xl)}getViewport(e){return this._viewports[e]}getFrameExtents(){return this._frameExtents}dispose(){this.map&&this.map.dispose(),this.mapPass&&this.mapPass.dispose()}copy(e){return this.camera=e.camera.clone(),this.intensity=e.intensity,this.bias=e.bias,this.radius=e.radius,this.autoUpdate=e.autoUpdate,this.needsUpdate=e.needsUpdate,this.normalBias=e.normalBias,this.blurSamples=e.blurSamples,this.mapSize.copy(e.mapSize),this}clone(){return new this.constructor().copy(this)}toJSON(){let e={};return this.intensity!==1&&(e.intensity=this.intensity),this.bias!==0&&(e.bias=this.bias),this.normalBias!==0&&(e.normalBias=this.normalBias),this.radius!==1&&(e.radius=this.radius),(this.mapSize.x!==512||this.mapSize.y!==512)&&(e.mapSize=this.mapSize.toArray()),e.camera=this.camera.toJSON(!1).object,delete e.camera.matrix,e}};var os=class extends qr{constructor(e=-1,t=1,n=1,r=-1,s=.1,a=2e3){super(),this.isOrthographicCamera=!0,this.type="OrthographicCamera",this.zoom=1,this.view=null,this.left=e,this.right=t,this.top=n,this.bottom=r,this.near=s,this.far=a,this.updateProjectionMatrix()}copy(e,t){return super.copy(e,t),this.left=e.left,this.right=e.right,this.top=e.top,this.bottom=e.bottom,this.near=e.near,this.far=e.far,this.zoom=e.zoom,this.view=e.view===null?null:Object.assign({},e.view),this}setViewOffset(e,t,n,r,s,a){this.view===null&&(this.view={enabled:!0,fullWidth:1,fullHeight:1,offsetX:0,offsetY:0,width:1,height:1}),this.view.enabled=!0,this.view.fullWidth=e,this.view.fullHeight=t,this.view.offsetX=n,this.view.offsetY=r,this.view.width=s,this.view.height=a,this.updateProjectionMatrix()}clearViewOffset(){this.view!==null&&(this.view.enabled=!1),this.updateProjectionMatrix()}updateProjectionMatrix(){let e=(this.right-this.left)/(2*this.zoom),t=(this.top-this.bottom)/(2*this.zoom),n=(this.right+this.left)/2,r=(this.top+this.bottom)/2,s=n-e,a=n+e,o=r+t,l=r-t;if(this.view!==null&&this.view.enabled){let c=(this.right-this.left)/this.view.fullWidth/this.zoom,d=(this.top-this.bottom)/this.view.fullHeight/this.zoom;s+=c*this.view.offsetX,a=s+c*this.view.width,o-=d*this.view.offsetY,l=o-d*this.view.height}this.projectionMatrix.makeOrthographic(s,a,o,l,this.near,this.far,this.coordinateSystem,this.reversedDepth),this.projectionMatrixInverse.copy(this.projectionMatrix).invert()}toJSON(e){let t=super.toJSON(e);return t.object.zoom=this.zoom,t.object.left=this.left,t.object.right=this.right,t.object.top=this.top,t.object.bottom=this.bottom,t.object.near=this.near,t.object.far=this.far,this.view!==null&&(t.object.view=Object.assign({},this.view)),t}},El=class extends Sl{constructor(){super(new os(-5,5,5,-5,.5,500)),this.isDirectionalLightShadow=!0}},ls=class extends ss{constructor(e,t){super(e,t),this.isDirectionalLight=!0,this.type="DirectionalLight",this.position.copy(wt.DEFAULT_UP),this.updateMatrix(),this.target=new wt,this.shadow=new El}dispose(){this.shadow.dispose()}copy(e){return super.copy(e),this.target=e.target.clone(),this.shadow=e.shadow.clone(),this}};var Na=class extends Dt{constructor(e=[]){super(),this.isArrayCamera=!0,this.isMultiViewCamera=!1,this.cameras=e}};var Yl="\\[\\]\\.:\\/",uf=new RegExp("["+Yl+"]","g"),Zl="[^"+Yl+"]",hf="[^"+Yl.replace("\\.","")+"]",ff=/((?:WC+[\/:])*)/.source.replace("WC",Zl),pf=/(WCOD+)?/.source.replace("WCOD",hf),mf=/(?:\.(WC+)(?:\[(.+)\])?)?/.source.replace("WC",Zl),gf=/\.(WC+)(?:\[(.+)\])?/.source.replace("WC",Zl),xf=new RegExp("^"+ff+pf+mf+gf+"$"),_f=["material","materials","bones","map"],Tl=class{constructor(e,t,n){let r=n||rt.parseTrackName(t);this._targetGroup=e,this._bindings=e.subscribe_(t,r)}getValue(e,t){this.bind();let n=this._targetGroup.nCachedObjects_,r=this._bindings[n];r!==void 0&&r.getValue(e,t)}setValue(e,t){let n=this._bindings;for(let r=this._targetGroup.nCachedObjects_,s=n.length;r!==s;++r)n[r].setValue(e,t)}bind(){let e=this._bindings;for(let t=this._targetGroup.nCachedObjects_,n=e.length;t!==n;++t)e[t].bind()}unbind(){let e=this._bindings;for(let t=this._targetGroup.nCachedObjects_,n=e.length;t!==n;++t)e[t].unbind()}},rt=class i{constructor(e,t,n){this.path=t,this.parsedPath=n||i.parseTrackName(t),this.node=i.findNode(e,this.parsedPath.nodeName),this.rootNode=e,this.getValue=this._getValue_unbound,this.setValue=this._setValue_unbound}static create(e,t,n){return e&&e.isAnimationObjectGroup?new i.Composite(e,t,n):new i(e,t,n)}static sanitizeNodeName(e){return e.replace(/\s/g,"_").replace(uf,"")}static parseTrackName(e){let t=xf.exec(e);if(t===null)throw new Error("PropertyBinding: Cannot parse trackName: "+e);let n={nodeName:t[2],objectName:t[3],objectIndex:t[4],propertyName:t[5],propertyIndex:t[6]},r=n.nodeName&&n.nodeName.lastIndexOf(".");if(r!==void 0&&r!==-1){let s=n.nodeName.substring(r+1);_f.indexOf(s)!==-1&&(n.nodeName=n.nodeName.substring(0,r),n.objectName=s)}if(n.propertyName===null||n.propertyName.length===0)throw new Error("PropertyBinding: can not parse propertyName from trackName: "+e);return n}static findNode(e,t){if(t===void 0||t===""||t==="."||t===-1||t===e.name||t===e.uuid)return e;if(e.skeleton){let n=e.skeleton.getBoneByName(t);if(n!==void 0)return n}if(e.children){let n=function(s){for(let a=0;a<s.length;a++){let o=s[a];if(o.name===t||o.uuid===t)return o;let l=n(o.children);if(l)return l}return null},r=n(e.children);if(r)return r}return null}_getValue_unavailable(){}_setValue_unavailable(){}_getValue_direct(e,t){e[t]=this.targetObject[this.propertyName]}_getValue_array(e,t){let n=this.resolvedProperty;for(let r=0,s=n.length;r!==s;++r)e[t++]=n[r]}_getValue_arrayElement(e,t){e[t]=this.resolvedProperty[this.propertyIndex]}_getValue_toArray(e,t){this.resolvedProperty.toArray(e,t)}_setValue_direct(e,t){this.targetObject[this.propertyName]=e[t]}_setValue_direct_setNeedsUpdate(e,t){this.targetObject[this.propertyName]=e[t],this.targetObject.needsUpdate=!0}_setValue_direct_setMatrixWorldNeedsUpdate(e,t){this.targetObject[this.propertyName]=e[t],this.targetObject.matrixWorldNeedsUpdate=!0}_setValue_array(e,t){let n=this.resolvedProperty;for(let r=0,s=n.length;r!==s;++r)n[r]=e[t++]}_setValue_array_setNeedsUpdate(e,t){let n=this.resolvedProperty;for(let r=0,s=n.length;r!==s;++r)n[r]=e[t++];this.targetObject.needsUpdate=!0}_setValue_array_setMatrixWorldNeedsUpdate(e,t){let n=this.resolvedProperty;for(let r=0,s=n.length;r!==s;++r)n[r]=e[t++];this.targetObject.matrixWorldNeedsUpdate=!0}_setValue_arrayElement(e,t){this.resolvedProperty[this.propertyIndex]=e[t]}_setValue_arrayElement_setNeedsUpdate(e,t){this.resolvedProperty[this.propertyIndex]=e[t],this.targetObject.needsUpdate=!0}_setValue_arrayElement_setMatrixWorldNeedsUpdate(e,t){this.resolvedProperty[this.propertyIndex]=e[t],this.targetObject.matrixWorldNeedsUpdate=!0}_setValue_fromArray(e,t){this.resolvedProperty.fromArray(e,t)}_setValue_fromArray_setNeedsUpdate(e,t){this.resolvedProperty.fromArray(e,t),this.targetObject.needsUpdate=!0}_setValue_fromArray_setMatrixWorldNeedsUpdate(e,t){this.resolvedProperty.fromArray(e,t),this.targetObject.matrixWorldNeedsUpdate=!0}_getValue_unbound(e,t){this.bind(),this.getValue(e,t)}_setValue_unbound(e,t){this.bind(),this.setValue(e,t)}bind(){let e=this.node,t=this.parsedPath,n=t.objectName,r=t.propertyName,s=t.propertyIndex;if(e||(e=i.findNode(this.rootNode,t.nodeName),this.node=e),this.getValue=this._getValue_unavailable,this.setValue=this._setValue_unavailable,!e){console.warn("THREE.PropertyBinding: No target node found for track: "+this.path+".");return}if(n){let c=t.objectIndex;switch(n){case"materials":if(!e.material){console.error("THREE.PropertyBinding: Can not bind to material as node does not have a material.",this);return}if(!e.material.materials){console.error("THREE.PropertyBinding: Can not bind to material.materials as node.material does not have a materials array.",this);return}e=e.material.materials;break;case"bones":if(!e.skeleton){console.error("THREE.PropertyBinding: Can not bind to bones as node does not have a skeleton.",this);return}e=e.skeleton.bones;for(let d=0;d<e.length;d++)if(e[d].name===c){c=d;break}break;case"map":if("map"in e){e=e.map;break}if(!e.material){console.error("THREE.PropertyBinding: Can not bind to material as node does not have a material.",this);return}if(!e.material.map){console.error("THREE.PropertyBinding: Can not bind to material.map as node.material does not have a map.",this);return}e=e.material.map;break;default:if(e[n]===void 0){console.error("THREE.PropertyBinding: Can not bind to objectName of node undefined.",this);return}e=e[n]}if(c!==void 0){if(e[c]===void 0){console.error("THREE.PropertyBinding: Trying to bind to objectIndex of objectName, but is undefined.",this,e);return}e=e[c]}}let a=e[r];if(a===void 0){let c=t.nodeName;console.error("THREE.PropertyBinding: Trying to update property for track: "+c+"."+r+" but it wasn't found.",e);return}let o=this.Versioning.None;this.targetObject=e,e.isMaterial===!0?o=this.Versioning.NeedsUpdate:e.isObject3D===!0&&(o=this.Versioning.MatrixWorldNeedsUpdate);let l=this.BindingType.Direct;if(s!==void 0){if(r==="morphTargetInfluences"){if(!e.geometry){console.error("THREE.PropertyBinding: Can not bind to morphTargetInfluences because node does not have a geometry.",this);return}if(!e.geometry.morphAttributes){console.error("THREE.PropertyBinding: Can not bind to morphTargetInfluences because node does not have a geometry.morphAttributes.",this);return}e.morphTargetDictionary[s]!==void 0&&(s=e.morphTargetDictionary[s])}l=this.BindingType.ArrayElement,this.resolvedProperty=a,this.propertyIndex=s}else a.fromArray!==void 0&&a.toArray!==void 0?(l=this.BindingType.HasFromToArray,this.resolvedProperty=a):Array.isArray(a)?(l=this.BindingType.EntireArray,this.resolvedProperty=a):this.propertyName=r;this.getValue=this.GetterByBindingType[l],this.setValue=this.SetterByBindingTypeAndVersioning[l][o]}unbind(){this.node=null,this.getValue=this._getValue_unbound,this.setValue=this._setValue_unbound}};rt.Composite=Tl;rt.prototype.BindingType={Direct:0,EntireArray:1,ArrayElement:2,HasFromToArray:3};rt.prototype.Versioning={None:0,NeedsUpdate:1,MatrixWorldNeedsUpdate:2};rt.prototype.GetterByBindingType=[rt.prototype._getValue_direct,rt.prototype._getValue_array,rt.prototype._getValue_arrayElement,rt.prototype._getValue_toArray];rt.prototype.SetterByBindingTypeAndVersioning=[[rt.prototype._setValue_direct,rt.prototype._setValue_direct_setNeedsUpdate,rt.prototype._setValue_direct_setMatrixWorldNeedsUpdate],[rt.prototype._setValue_array,rt.prototype._setValue_array_setNeedsUpdate,rt.prototype._setValue_array_setMatrixWorldNeedsUpdate],[rt.prototype._setValue_arrayElement,rt.prototype._setValue_arrayElement_setNeedsUpdate,rt.prototype._setValue_arrayElement_setMatrixWorldNeedsUpdate],[rt.prototype._setValue_fromArray,rt.prototype._setValue_fromArray_setNeedsUpdate,rt.prototype._setValue_fromArray_setMatrixWorldNeedsUpdate]];var Tx=new Float32Array(1);var cs=class{constructor(e=1,t=0,n=0){this.radius=e,this.phi=t,this.theta=n}set(e,t,n){return this.radius=e,this.phi=t,this.theta=n,this}copy(e){return this.radius=e.radius,this.phi=e.phi,this.theta=e.theta,this}makeSafe(){return this.phi=Ge(this.phi,1e-6,Math.PI-1e-6),this}setFromVector3(e){return this.setFromCartesianCoords(e.x,e.y,e.z)}setFromCartesianCoords(e,t,n){return this.radius=Math.sqrt(e*e+t*t+n*n),this.radius===0?(this.theta=0,this.phi=0):(this.theta=Math.atan2(e,n),this.phi=Math.acos(Ge(t/this.radius,-1,1))),this}clone(){return new this.constructor().copy(this)}};var ds=class extends oi{constructor(e=10,t=10,n=4473924,r=8947848){n=new Ne(n),r=new Ne(r);let s=t/2,a=e/t,o=e/2,l=[],c=[];for(let h=0,p=0,g=-o;h<=t;h++,g+=a){l.push(-o,0,g,o,0,g),l.push(g,0,-o,g,0,o);let x=h===s?n:r;x.toArray(c,p),p+=3,x.toArray(c,p),p+=3,x.toArray(c,p),p+=3,x.toArray(c,p),p+=3}let d=new dt;d.setAttribute("position",new je(l,3)),d.setAttribute("color",new je(c,3));let u=new nn({vertexColors:!0,toneMapped:!1});super(d,u),this.type="GridHelper"}dispose(){this.geometry.dispose(),this.material.dispose()}};var hd=new N,ra,_l,us=class extends wt{constructor(e=new N(0,0,1),t=new N(0,0,0),n=1,r=16776960,s=n*.2,a=s*.2){super(),this.type="ArrowHelper",ra===void 0&&(ra=new dt,ra.setAttribute("position",new je([0,0,0,0,1,0],3)),_l=new mr(.5,1,5,1),_l.translate(0,-.5,0)),this.position.copy(t),this.line=new Wn(ra,new nn({color:r,toneMapped:!1})),this.line.matrixAutoUpdate=!1,this.add(this.line),this.cone=new st(_l,new Xt({color:r,toneMapped:!1})),this.cone.matrixAutoUpdate=!1,this.add(this.cone),this.setDirection(e),this.setLength(n,s,a)}setDirection(e){if(e.y>.99999)this.quaternion.set(0,0,0,1);else if(e.y<-.99999)this.quaternion.set(1,0,0,0);else{hd.set(e.z,0,-e.x).normalize();let t=Math.acos(e.y);this.quaternion.setFromAxisAngle(hd,t)}}setLength(e,t=e*.2,n=t*.2){this.line.scale.set(1,Math.max(1e-4,e-t),1),this.line.updateMatrix(),this.cone.scale.set(n,t,n),this.cone.position.y=e,this.cone.updateMatrix()}setColor(e){this.line.material.color.set(e),this.cone.material.color.set(e)}copy(e){return super.copy(e,!1),this.line.copy(e.line),this.cone.copy(e.cone),this}dispose(){this.line.geometry.dispose(),this.line.material.dispose(),this.cone.geometry.dispose(),this.cone.material.dispose()}};function Jl(i,e,t,n){let r=yf(n);switch(t){case Bl:return i*e;case kl:return i*e/r.components*r.byteLength;case $a:return i*e/r.components*r.byteLength;case Hl:return i*e*2/r.components*r.byteLength;case qa:return i*e*2/r.components*r.byteLength;case zl:return i*e*3/r.components*r.byteLength;case un:return i*e*4/r.components*r.byteLength;case Ya:return i*e*4/r.components*r.byteLength;case ps:case ms:return Math.floor((i+3)/4)*Math.floor((e+3)/4)*8;case gs:case xs:return Math.floor((i+3)/4)*Math.floor((e+3)/4)*16;case Ja:case ja:return Math.max(i,16)*Math.max(e,8)/4;case Za:case Ka:return Math.max(i,8)*Math.max(e,8)/2;case Qa:case eo:return Math.floor((i+3)/4)*Math.floor((e+3)/4)*8;case to:return Math.floor((i+3)/4)*Math.floor((e+3)/4)*16;case no:return Math.floor((i+3)/4)*Math.floor((e+3)/4)*16;case io:return Math.floor((i+4)/5)*Math.floor((e+3)/4)*16;case ro:return Math.floor((i+4)/5)*Math.floor((e+4)/5)*16;case so:return Math.floor((i+5)/6)*Math.floor((e+4)/5)*16;case ao:return Math.floor((i+5)/6)*Math.floor((e+5)/6)*16;case oo:return Math.floor((i+7)/8)*Math.floor((e+4)/5)*16;case lo:return Math.floor((i+7)/8)*Math.floor((e+5)/6)*16;case co:return Math.floor((i+7)/8)*Math.floor((e+7)/8)*16;case uo:return Math.floor((i+9)/10)*Math.floor((e+4)/5)*16;case ho:return Math.floor((i+9)/10)*Math.floor((e+5)/6)*16;case fo:return Math.floor((i+9)/10)*Math.floor((e+7)/8)*16;case po:return Math.floor((i+9)/10)*Math.floor((e+9)/10)*16;case mo:return Math.floor((i+11)/12)*Math.floor((e+9)/10)*16;case go:return Math.floor((i+11)/12)*Math.floor((e+11)/12)*16;case xo:case _o:case yo:return Math.ceil(i/4)*Math.ceil(e/4)*16;case vo:case bo:return Math.ceil(i/4)*Math.ceil(e/4)*8;case wo:case Mo:return Math.ceil(i/4)*Math.ceil(e/4)*16}throw new Error(`Unable to determine texture byte length for ${t} format.`)}function yf(i){switch(i){case Mn:case Ll:return{byteLength:1,components:1};case gr:case Fl:case xr:return{byteLength:2,components:1};case Wa:case Xa:return{byteLength:2,components:4};case hi:case Ga:case Pn:return{byteLength:4,components:1};case Ul:case Ol:return{byteLength:4,components:3}}throw new Error(`Unknown texture type ${i}.`)}typeof __THREE_DEVTOOLS__<"u"&&__THREE_DEVTOOLS__.dispatchEvent(new CustomEvent("register",{detail:{revision:"180"}}));typeof window<"u"&&(window.__THREE__?console.warn("WARNING: Multiple instances of Three.js being imported."):window.__THREE__="180");function Ru(){let i=null,e=!1,t=null,n=null;function r(s,a){t(s,a),n=i.requestAnimationFrame(r)}return{start:function(){e!==!0&&t!==null&&(n=i.requestAnimationFrame(r),e=!0)},stop:function(){i.cancelAnimationFrame(n),e=!1},setAnimationLoop:function(s){t=s},setContext:function(s){i=s}}}function bf(i){let e=new WeakMap;function t(o,l){let c=o.array,d=o.usage,u=c.byteLength,h=i.createBuffer();i.bindBuffer(l,h),i.bufferData(l,c,d),o.onUploadCallback();let p;if(c instanceof Float32Array)p=i.FLOAT;else if(typeof Float16Array<"u"&&c instanceof Float16Array)p=i.HALF_FLOAT;else if(c instanceof Uint16Array)o.isFloat16BufferAttribute?p=i.HALF_FLOAT:p=i.UNSIGNED_SHORT;else if(c instanceof Int16Array)p=i.SHORT;else if(c instanceof Uint32Array)p=i.UNSIGNED_INT;else if(c instanceof Int32Array)p=i.INT;else if(c instanceof Int8Array)p=i.BYTE;else if(c instanceof Uint8Array)p=i.UNSIGNED_BYTE;else if(c instanceof Uint8ClampedArray)p=i.UNSIGNED_BYTE;else throw new Error("THREE.WebGLAttributes: Unsupported buffer data format: "+c);return{buffer:h,type:p,bytesPerElement:c.BYTES_PER_ELEMENT,version:o.version,size:u}}function n(o,l,c){let d=l.array,u=l.updateRanges;if(i.bindBuffer(c,o),u.length===0)i.bufferSubData(c,0,d);else{u.sort((p,g)=>p.start-g.start);let h=0;for(let p=1;p<u.length;p++){let g=u[h],x=u[p];x.start<=g.start+g.count+1?g.count=Math.max(g.count,x.start+x.count-g.start):(++h,u[h]=x)}u.length=h+1;for(let p=0,g=u.length;p<g;p++){let x=u[p];i.bufferSubData(c,x.start*d.BYTES_PER_ELEMENT,d,x.start,x.count)}l.clearUpdateRanges()}l.onUploadCallback()}function r(o){return o.isInterleavedBufferAttribute&&(o=o.data),e.get(o)}function s(o){o.isInterleavedBufferAttribute&&(o=o.data);let l=e.get(o);l&&(i.deleteBuffer(l.buffer),e.delete(o))}function a(o,l){if(o.isInterleavedBufferAttribute&&(o=o.data),o.isGLBufferAttribute){let d=e.get(o);(!d||d.version<o.version)&&e.set(o,{buffer:o.buffer,type:o.type,bytesPerElement:o.elementSize,version:o.version});return}let c=e.get(o);if(c===void 0)e.set(o,t(o,l));else if(c.version<o.version){if(c.size!==o.array.byteLength)throw new Error("THREE.WebGLAttributes: The size of the buffer attribute's array buffer does not match the original size. Resizing buffer attributes is not supported.");n(c.buffer,o,l),c.version=o.version}}return{get:r,remove:s,update:a}}var wf=`#ifdef USE_ALPHAHASH
	if ( diffuseColor.a < getAlphaHashThreshold( vPosition ) ) discard;
#endif`,Mf=`#ifdef USE_ALPHAHASH
	const float ALPHA_HASH_SCALE = 0.05;
	float hash2D( vec2 value ) {
		return fract( 1.0e4 * sin( 17.0 * value.x + 0.1 * value.y ) * ( 0.1 + abs( sin( 13.0 * value.y + value.x ) ) ) );
	}
	float hash3D( vec3 value ) {
		return hash2D( vec2( hash2D( value.xy ), value.z ) );
	}
	float getAlphaHashThreshold( vec3 position ) {
		float maxDeriv = max(
			length( dFdx( position.xyz ) ),
			length( dFdy( position.xyz ) )
		);
		float pixScale = 1.0 / ( ALPHA_HASH_SCALE * maxDeriv );
		vec2 pixScales = vec2(
			exp2( floor( log2( pixScale ) ) ),
			exp2( ceil( log2( pixScale ) ) )
		);
		vec2 alpha = vec2(
			hash3D( floor( pixScales.x * position.xyz ) ),
			hash3D( floor( pixScales.y * position.xyz ) )
		);
		float lerpFactor = fract( log2( pixScale ) );
		float x = ( 1.0 - lerpFactor ) * alpha.x + lerpFactor * alpha.y;
		float a = min( lerpFactor, 1.0 - lerpFactor );
		vec3 cases = vec3(
			x * x / ( 2.0 * a * ( 1.0 - a ) ),
			( x - 0.5 * a ) / ( 1.0 - a ),
			1.0 - ( ( 1.0 - x ) * ( 1.0 - x ) / ( 2.0 * a * ( 1.0 - a ) ) )
		);
		float threshold = ( x < ( 1.0 - a ) )
			? ( ( x < a ) ? cases.x : cases.y )
			: cases.z;
		return clamp( threshold , 1.0e-6, 1.0 );
	}
#endif`,Sf=`#ifdef USE_ALPHAMAP
	diffuseColor.a *= texture2D( alphaMap, vAlphaMapUv ).g;
#endif`,Ef=`#ifdef USE_ALPHAMAP
	uniform sampler2D alphaMap;
#endif`,Tf=`#ifdef USE_ALPHATEST
	#ifdef ALPHA_TO_COVERAGE
	diffuseColor.a = smoothstep( alphaTest, alphaTest + fwidth( diffuseColor.a ), diffuseColor.a );
	if ( diffuseColor.a == 0.0 ) discard;
	#else
	if ( diffuseColor.a < alphaTest ) discard;
	#endif
#endif`,Af=`#ifdef USE_ALPHATEST
	uniform float alphaTest;
#endif`,Cf=`#ifdef USE_AOMAP
	float ambientOcclusion = ( texture2D( aoMap, vAoMapUv ).r - 1.0 ) * aoMapIntensity + 1.0;
	reflectedLight.indirectDiffuse *= ambientOcclusion;
	#if defined( USE_CLEARCOAT ) 
		clearcoatSpecularIndirect *= ambientOcclusion;
	#endif
	#if defined( USE_SHEEN ) 
		sheenSpecularIndirect *= ambientOcclusion;
	#endif
	#if defined( USE_ENVMAP ) && defined( STANDARD )
		float dotNV = saturate( dot( geometryNormal, geometryViewDir ) );
		reflectedLight.indirectSpecular *= computeSpecularOcclusion( dotNV, ambientOcclusion, material.roughness );
	#endif
#endif`,Rf=`#ifdef USE_AOMAP
	uniform sampler2D aoMap;
	uniform float aoMapIntensity;
#endif`,If=`#ifdef USE_BATCHING
	#if ! defined( GL_ANGLE_multi_draw )
	#define gl_DrawID _gl_DrawID
	uniform int _gl_DrawID;
	#endif
	uniform highp sampler2D batchingTexture;
	uniform highp usampler2D batchingIdTexture;
	mat4 getBatchingMatrix( const in float i ) {
		int size = textureSize( batchingTexture, 0 ).x;
		int j = int( i ) * 4;
		int x = j % size;
		int y = j / size;
		vec4 v1 = texelFetch( batchingTexture, ivec2( x, y ), 0 );
		vec4 v2 = texelFetch( batchingTexture, ivec2( x + 1, y ), 0 );
		vec4 v3 = texelFetch( batchingTexture, ivec2( x + 2, y ), 0 );
		vec4 v4 = texelFetch( batchingTexture, ivec2( x + 3, y ), 0 );
		return mat4( v1, v2, v3, v4 );
	}
	float getIndirectIndex( const in int i ) {
		int size = textureSize( batchingIdTexture, 0 ).x;
		int x = i % size;
		int y = i / size;
		return float( texelFetch( batchingIdTexture, ivec2( x, y ), 0 ).r );
	}
#endif
#ifdef USE_BATCHING_COLOR
	uniform sampler2D batchingColorTexture;
	vec3 getBatchingColor( const in float i ) {
		int size = textureSize( batchingColorTexture, 0 ).x;
		int j = int( i );
		int x = j % size;
		int y = j / size;
		return texelFetch( batchingColorTexture, ivec2( x, y ), 0 ).rgb;
	}
#endif`,Pf=`#ifdef USE_BATCHING
	mat4 batchingMatrix = getBatchingMatrix( getIndirectIndex( gl_DrawID ) );
#endif`,Nf=`vec3 transformed = vec3( position );
#ifdef USE_ALPHAHASH
	vPosition = vec3( position );
#endif`,Df=`vec3 objectNormal = vec3( normal );
#ifdef USE_TANGENT
	vec3 objectTangent = vec3( tangent.xyz );
#endif`,Lf=`float G_BlinnPhong_Implicit( ) {
	return 0.25;
}
float D_BlinnPhong( const in float shininess, const in float dotNH ) {
	return RECIPROCAL_PI * ( shininess * 0.5 + 1.0 ) * pow( dotNH, shininess );
}
vec3 BRDF_BlinnPhong( const in vec3 lightDir, const in vec3 viewDir, const in vec3 normal, const in vec3 specularColor, const in float shininess ) {
	vec3 halfDir = normalize( lightDir + viewDir );
	float dotNH = saturate( dot( normal, halfDir ) );
	float dotVH = saturate( dot( viewDir, halfDir ) );
	vec3 F = F_Schlick( specularColor, 1.0, dotVH );
	float G = G_BlinnPhong_Implicit( );
	float D = D_BlinnPhong( shininess, dotNH );
	return F * ( G * D );
} // validated`,Ff=`#ifdef USE_IRIDESCENCE
	const mat3 XYZ_TO_REC709 = mat3(
		 3.2404542, -0.9692660,  0.0556434,
		-1.5371385,  1.8760108, -0.2040259,
		-0.4985314,  0.0415560,  1.0572252
	);
	vec3 Fresnel0ToIor( vec3 fresnel0 ) {
		vec3 sqrtF0 = sqrt( fresnel0 );
		return ( vec3( 1.0 ) + sqrtF0 ) / ( vec3( 1.0 ) - sqrtF0 );
	}
	vec3 IorToFresnel0( vec3 transmittedIor, float incidentIor ) {
		return pow2( ( transmittedIor - vec3( incidentIor ) ) / ( transmittedIor + vec3( incidentIor ) ) );
	}
	float IorToFresnel0( float transmittedIor, float incidentIor ) {
		return pow2( ( transmittedIor - incidentIor ) / ( transmittedIor + incidentIor ));
	}
	vec3 evalSensitivity( float OPD, vec3 shift ) {
		float phase = 2.0 * PI * OPD * 1.0e-9;
		vec3 val = vec3( 5.4856e-13, 4.4201e-13, 5.2481e-13 );
		vec3 pos = vec3( 1.6810e+06, 1.7953e+06, 2.2084e+06 );
		vec3 var = vec3( 4.3278e+09, 9.3046e+09, 6.6121e+09 );
		vec3 xyz = val * sqrt( 2.0 * PI * var ) * cos( pos * phase + shift ) * exp( - pow2( phase ) * var );
		xyz.x += 9.7470e-14 * sqrt( 2.0 * PI * 4.5282e+09 ) * cos( 2.2399e+06 * phase + shift[ 0 ] ) * exp( - 4.5282e+09 * pow2( phase ) );
		xyz /= 1.0685e-7;
		vec3 rgb = XYZ_TO_REC709 * xyz;
		return rgb;
	}
	vec3 evalIridescence( float outsideIOR, float eta2, float cosTheta1, float thinFilmThickness, vec3 baseF0 ) {
		vec3 I;
		float iridescenceIOR = mix( outsideIOR, eta2, smoothstep( 0.0, 0.03, thinFilmThickness ) );
		float sinTheta2Sq = pow2( outsideIOR / iridescenceIOR ) * ( 1.0 - pow2( cosTheta1 ) );
		float cosTheta2Sq = 1.0 - sinTheta2Sq;
		if ( cosTheta2Sq < 0.0 ) {
			return vec3( 1.0 );
		}
		float cosTheta2 = sqrt( cosTheta2Sq );
		float R0 = IorToFresnel0( iridescenceIOR, outsideIOR );
		float R12 = F_Schlick( R0, 1.0, cosTheta1 );
		float T121 = 1.0 - R12;
		float phi12 = 0.0;
		if ( iridescenceIOR < outsideIOR ) phi12 = PI;
		float phi21 = PI - phi12;
		vec3 baseIOR = Fresnel0ToIor( clamp( baseF0, 0.0, 0.9999 ) );		vec3 R1 = IorToFresnel0( baseIOR, iridescenceIOR );
		vec3 R23 = F_Schlick( R1, 1.0, cosTheta2 );
		vec3 phi23 = vec3( 0.0 );
		if ( baseIOR[ 0 ] < iridescenceIOR ) phi23[ 0 ] = PI;
		if ( baseIOR[ 1 ] < iridescenceIOR ) phi23[ 1 ] = PI;
		if ( baseIOR[ 2 ] < iridescenceIOR ) phi23[ 2 ] = PI;
		float OPD = 2.0 * iridescenceIOR * thinFilmThickness * cosTheta2;
		vec3 phi = vec3( phi21 ) + phi23;
		vec3 R123 = clamp( R12 * R23, 1e-5, 0.9999 );
		vec3 r123 = sqrt( R123 );
		vec3 Rs = pow2( T121 ) * R23 / ( vec3( 1.0 ) - R123 );
		vec3 C0 = R12 + Rs;
		I = C0;
		vec3 Cm = Rs - T121;
		for ( int m = 1; m <= 2; ++ m ) {
			Cm *= r123;
			vec3 Sm = 2.0 * evalSensitivity( float( m ) * OPD, float( m ) * phi );
			I += Cm * Sm;
		}
		return max( I, vec3( 0.0 ) );
	}
#endif`,Uf=`#ifdef USE_BUMPMAP
	uniform sampler2D bumpMap;
	uniform float bumpScale;
	vec2 dHdxy_fwd() {
		vec2 dSTdx = dFdx( vBumpMapUv );
		vec2 dSTdy = dFdy( vBumpMapUv );
		float Hll = bumpScale * texture2D( bumpMap, vBumpMapUv ).x;
		float dBx = bumpScale * texture2D( bumpMap, vBumpMapUv + dSTdx ).x - Hll;
		float dBy = bumpScale * texture2D( bumpMap, vBumpMapUv + dSTdy ).x - Hll;
		return vec2( dBx, dBy );
	}
	vec3 perturbNormalArb( vec3 surf_pos, vec3 surf_norm, vec2 dHdxy, float faceDirection ) {
		vec3 vSigmaX = normalize( dFdx( surf_pos.xyz ) );
		vec3 vSigmaY = normalize( dFdy( surf_pos.xyz ) );
		vec3 vN = surf_norm;
		vec3 R1 = cross( vSigmaY, vN );
		vec3 R2 = cross( vN, vSigmaX );
		float fDet = dot( vSigmaX, R1 ) * faceDirection;
		vec3 vGrad = sign( fDet ) * ( dHdxy.x * R1 + dHdxy.y * R2 );
		return normalize( abs( fDet ) * surf_norm - vGrad );
	}
#endif`,Of=`#if NUM_CLIPPING_PLANES > 0
	vec4 plane;
	#ifdef ALPHA_TO_COVERAGE
		float distanceToPlane, distanceGradient;
		float clipOpacity = 1.0;
		#pragma unroll_loop_start
		for ( int i = 0; i < UNION_CLIPPING_PLANES; i ++ ) {
			plane = clippingPlanes[ i ];
			distanceToPlane = - dot( vClipPosition, plane.xyz ) + plane.w;
			distanceGradient = fwidth( distanceToPlane ) / 2.0;
			clipOpacity *= smoothstep( - distanceGradient, distanceGradient, distanceToPlane );
			if ( clipOpacity == 0.0 ) discard;
		}
		#pragma unroll_loop_end
		#if UNION_CLIPPING_PLANES < NUM_CLIPPING_PLANES
			float unionClipOpacity = 1.0;
			#pragma unroll_loop_start
			for ( int i = UNION_CLIPPING_PLANES; i < NUM_CLIPPING_PLANES; i ++ ) {
				plane = clippingPlanes[ i ];
				distanceToPlane = - dot( vClipPosition, plane.xyz ) + plane.w;
				distanceGradient = fwidth( distanceToPlane ) / 2.0;
				unionClipOpacity *= 1.0 - smoothstep( - distanceGradient, distanceGradient, distanceToPlane );
			}
			#pragma unroll_loop_end
			clipOpacity *= 1.0 - unionClipOpacity;
		#endif
		diffuseColor.a *= clipOpacity;
		if ( diffuseColor.a == 0.0 ) discard;
	#else
		#pragma unroll_loop_start
		for ( int i = 0; i < UNION_CLIPPING_PLANES; i ++ ) {
			plane = clippingPlanes[ i ];
			if ( dot( vClipPosition, plane.xyz ) > plane.w ) discard;
		}
		#pragma unroll_loop_end
		#if UNION_CLIPPING_PLANES < NUM_CLIPPING_PLANES
			bool clipped = true;
			#pragma unroll_loop_start
			for ( int i = UNION_CLIPPING_PLANES; i < NUM_CLIPPING_PLANES; i ++ ) {
				plane = clippingPlanes[ i ];
				clipped = ( dot( vClipPosition, plane.xyz ) > plane.w ) && clipped;
			}
			#pragma unroll_loop_end
			if ( clipped ) discard;
		#endif
	#endif
#endif`,Bf=`#if NUM_CLIPPING_PLANES > 0
	varying vec3 vClipPosition;
	uniform vec4 clippingPlanes[ NUM_CLIPPING_PLANES ];
#endif`,zf=`#if NUM_CLIPPING_PLANES > 0
	varying vec3 vClipPosition;
#endif`,kf=`#if NUM_CLIPPING_PLANES > 0
	vClipPosition = - mvPosition.xyz;
#endif`,Hf=`#if defined( USE_COLOR_ALPHA )
	diffuseColor *= vColor;
#elif defined( USE_COLOR )
	diffuseColor.rgb *= vColor;
#endif`,Vf=`#if defined( USE_COLOR_ALPHA )
	varying vec4 vColor;
#elif defined( USE_COLOR )
	varying vec3 vColor;
#endif`,Gf=`#if defined( USE_COLOR_ALPHA )
	varying vec4 vColor;
#elif defined( USE_COLOR ) || defined( USE_INSTANCING_COLOR ) || defined( USE_BATCHING_COLOR )
	varying vec3 vColor;
#endif`,Wf=`#if defined( USE_COLOR_ALPHA )
	vColor = vec4( 1.0 );
#elif defined( USE_COLOR ) || defined( USE_INSTANCING_COLOR ) || defined( USE_BATCHING_COLOR )
	vColor = vec3( 1.0 );
#endif
#ifdef USE_COLOR
	vColor *= color;
#endif
#ifdef USE_INSTANCING_COLOR
	vColor.xyz *= instanceColor.xyz;
#endif
#ifdef USE_BATCHING_COLOR
	vec3 batchingColor = getBatchingColor( getIndirectIndex( gl_DrawID ) );
	vColor.xyz *= batchingColor.xyz;
#endif`,Xf=`#define PI 3.141592653589793
#define PI2 6.283185307179586
#define PI_HALF 1.5707963267948966
#define RECIPROCAL_PI 0.3183098861837907
#define RECIPROCAL_PI2 0.15915494309189535
#define EPSILON 1e-6
#ifndef saturate
#define saturate( a ) clamp( a, 0.0, 1.0 )
#endif
#define whiteComplement( a ) ( 1.0 - saturate( a ) )
float pow2( const in float x ) { return x*x; }
vec3 pow2( const in vec3 x ) { return x*x; }
float pow3( const in float x ) { return x*x*x; }
float pow4( const in float x ) { float x2 = x*x; return x2*x2; }
float max3( const in vec3 v ) { return max( max( v.x, v.y ), v.z ); }
float average( const in vec3 v ) { return dot( v, vec3( 0.3333333 ) ); }
highp float rand( const in vec2 uv ) {
	const highp float a = 12.9898, b = 78.233, c = 43758.5453;
	highp float dt = dot( uv.xy, vec2( a,b ) ), sn = mod( dt, PI );
	return fract( sin( sn ) * c );
}
#ifdef HIGH_PRECISION
	float precisionSafeLength( vec3 v ) { return length( v ); }
#else
	float precisionSafeLength( vec3 v ) {
		float maxComponent = max3( abs( v ) );
		return length( v / maxComponent ) * maxComponent;
	}
#endif
struct IncidentLight {
	vec3 color;
	vec3 direction;
	bool visible;
};
struct ReflectedLight {
	vec3 directDiffuse;
	vec3 directSpecular;
	vec3 indirectDiffuse;
	vec3 indirectSpecular;
};
#ifdef USE_ALPHAHASH
	varying vec3 vPosition;
#endif
vec3 transformDirection( in vec3 dir, in mat4 matrix ) {
	return normalize( ( matrix * vec4( dir, 0.0 ) ).xyz );
}
vec3 inverseTransformDirection( in vec3 dir, in mat4 matrix ) {
	return normalize( ( vec4( dir, 0.0 ) * matrix ).xyz );
}
mat3 transposeMat3( const in mat3 m ) {
	mat3 tmp;
	tmp[ 0 ] = vec3( m[ 0 ].x, m[ 1 ].x, m[ 2 ].x );
	tmp[ 1 ] = vec3( m[ 0 ].y, m[ 1 ].y, m[ 2 ].y );
	tmp[ 2 ] = vec3( m[ 0 ].z, m[ 1 ].z, m[ 2 ].z );
	return tmp;
}
bool isPerspectiveMatrix( mat4 m ) {
	return m[ 2 ][ 3 ] == - 1.0;
}
vec2 equirectUv( in vec3 dir ) {
	float u = atan( dir.z, dir.x ) * RECIPROCAL_PI2 + 0.5;
	float v = asin( clamp( dir.y, - 1.0, 1.0 ) ) * RECIPROCAL_PI + 0.5;
	return vec2( u, v );
}
vec3 BRDF_Lambert( const in vec3 diffuseColor ) {
	return RECIPROCAL_PI * diffuseColor;
}
vec3 F_Schlick( const in vec3 f0, const in float f90, const in float dotVH ) {
	float fresnel = exp2( ( - 5.55473 * dotVH - 6.98316 ) * dotVH );
	return f0 * ( 1.0 - fresnel ) + ( f90 * fresnel );
}
float F_Schlick( const in float f0, const in float f90, const in float dotVH ) {
	float fresnel = exp2( ( - 5.55473 * dotVH - 6.98316 ) * dotVH );
	return f0 * ( 1.0 - fresnel ) + ( f90 * fresnel );
} // validated`,$f=`#ifdef ENVMAP_TYPE_CUBE_UV
	#define cubeUV_minMipLevel 4.0
	#define cubeUV_minTileSize 16.0
	float getFace( vec3 direction ) {
		vec3 absDirection = abs( direction );
		float face = - 1.0;
		if ( absDirection.x > absDirection.z ) {
			if ( absDirection.x > absDirection.y )
				face = direction.x > 0.0 ? 0.0 : 3.0;
			else
				face = direction.y > 0.0 ? 1.0 : 4.0;
		} else {
			if ( absDirection.z > absDirection.y )
				face = direction.z > 0.0 ? 2.0 : 5.0;
			else
				face = direction.y > 0.0 ? 1.0 : 4.0;
		}
		return face;
	}
	vec2 getUV( vec3 direction, float face ) {
		vec2 uv;
		if ( face == 0.0 ) {
			uv = vec2( direction.z, direction.y ) / abs( direction.x );
		} else if ( face == 1.0 ) {
			uv = vec2( - direction.x, - direction.z ) / abs( direction.y );
		} else if ( face == 2.0 ) {
			uv = vec2( - direction.x, direction.y ) / abs( direction.z );
		} else if ( face == 3.0 ) {
			uv = vec2( - direction.z, direction.y ) / abs( direction.x );
		} else if ( face == 4.0 ) {
			uv = vec2( - direction.x, direction.z ) / abs( direction.y );
		} else {
			uv = vec2( direction.x, direction.y ) / abs( direction.z );
		}
		return 0.5 * ( uv + 1.0 );
	}
	vec3 bilinearCubeUV( sampler2D envMap, vec3 direction, float mipInt ) {
		float face = getFace( direction );
		float filterInt = max( cubeUV_minMipLevel - mipInt, 0.0 );
		mipInt = max( mipInt, cubeUV_minMipLevel );
		float faceSize = exp2( mipInt );
		highp vec2 uv = getUV( direction, face ) * ( faceSize - 2.0 ) + 1.0;
		if ( face > 2.0 ) {
			uv.y += faceSize;
			face -= 3.0;
		}
		uv.x += face * faceSize;
		uv.x += filterInt * 3.0 * cubeUV_minTileSize;
		uv.y += 4.0 * ( exp2( CUBEUV_MAX_MIP ) - faceSize );
		uv.x *= CUBEUV_TEXEL_WIDTH;
		uv.y *= CUBEUV_TEXEL_HEIGHT;
		#ifdef texture2DGradEXT
			return texture2DGradEXT( envMap, uv, vec2( 0.0 ), vec2( 0.0 ) ).rgb;
		#else
			return texture2D( envMap, uv ).rgb;
		#endif
	}
	#define cubeUV_r0 1.0
	#define cubeUV_m0 - 2.0
	#define cubeUV_r1 0.8
	#define cubeUV_m1 - 1.0
	#define cubeUV_r4 0.4
	#define cubeUV_m4 2.0
	#define cubeUV_r5 0.305
	#define cubeUV_m5 3.0
	#define cubeUV_r6 0.21
	#define cubeUV_m6 4.0
	float roughnessToMip( float roughness ) {
		float mip = 0.0;
		if ( roughness >= cubeUV_r1 ) {
			mip = ( cubeUV_r0 - roughness ) * ( cubeUV_m1 - cubeUV_m0 ) / ( cubeUV_r0 - cubeUV_r1 ) + cubeUV_m0;
		} else if ( roughness >= cubeUV_r4 ) {
			mip = ( cubeUV_r1 - roughness ) * ( cubeUV_m4 - cubeUV_m1 ) / ( cubeUV_r1 - cubeUV_r4 ) + cubeUV_m1;
		} else if ( roughness >= cubeUV_r5 ) {
			mip = ( cubeUV_r4 - roughness ) * ( cubeUV_m5 - cubeUV_m4 ) / ( cubeUV_r4 - cubeUV_r5 ) + cubeUV_m4;
		} else if ( roughness >= cubeUV_r6 ) {
			mip = ( cubeUV_r5 - roughness ) * ( cubeUV_m6 - cubeUV_m5 ) / ( cubeUV_r5 - cubeUV_r6 ) + cubeUV_m5;
		} else {
			mip = - 2.0 * log2( 1.16 * roughness );		}
		return mip;
	}
	vec4 textureCubeUV( sampler2D envMap, vec3 sampleDir, float roughness ) {
		float mip = clamp( roughnessToMip( roughness ), cubeUV_m0, CUBEUV_MAX_MIP );
		float mipF = fract( mip );
		float mipInt = floor( mip );
		vec3 color0 = bilinearCubeUV( envMap, sampleDir, mipInt );
		if ( mipF == 0.0 ) {
			return vec4( color0, 1.0 );
		} else {
			vec3 color1 = bilinearCubeUV( envMap, sampleDir, mipInt + 1.0 );
			return vec4( mix( color0, color1, mipF ), 1.0 );
		}
	}
#endif`,qf=`vec3 transformedNormal = objectNormal;
#ifdef USE_TANGENT
	vec3 transformedTangent = objectTangent;
#endif
#ifdef USE_BATCHING
	mat3 bm = mat3( batchingMatrix );
	transformedNormal /= vec3( dot( bm[ 0 ], bm[ 0 ] ), dot( bm[ 1 ], bm[ 1 ] ), dot( bm[ 2 ], bm[ 2 ] ) );
	transformedNormal = bm * transformedNormal;
	#ifdef USE_TANGENT
		transformedTangent = bm * transformedTangent;
	#endif
#endif
#ifdef USE_INSTANCING
	mat3 im = mat3( instanceMatrix );
	transformedNormal /= vec3( dot( im[ 0 ], im[ 0 ] ), dot( im[ 1 ], im[ 1 ] ), dot( im[ 2 ], im[ 2 ] ) );
	transformedNormal = im * transformedNormal;
	#ifdef USE_TANGENT
		transformedTangent = im * transformedTangent;
	#endif
#endif
transformedNormal = normalMatrix * transformedNormal;
#ifdef FLIP_SIDED
	transformedNormal = - transformedNormal;
#endif
#ifdef USE_TANGENT
	transformedTangent = ( modelViewMatrix * vec4( transformedTangent, 0.0 ) ).xyz;
	#ifdef FLIP_SIDED
		transformedTangent = - transformedTangent;
	#endif
#endif`,Yf=`#ifdef USE_DISPLACEMENTMAP
	uniform sampler2D displacementMap;
	uniform float displacementScale;
	uniform float displacementBias;
#endif`,Zf=`#ifdef USE_DISPLACEMENTMAP
	transformed += normalize( objectNormal ) * ( texture2D( displacementMap, vDisplacementMapUv ).x * displacementScale + displacementBias );
#endif`,Jf=`#ifdef USE_EMISSIVEMAP
	vec4 emissiveColor = texture2D( emissiveMap, vEmissiveMapUv );
	#ifdef DECODE_VIDEO_TEXTURE_EMISSIVE
		emissiveColor = sRGBTransferEOTF( emissiveColor );
	#endif
	totalEmissiveRadiance *= emissiveColor.rgb;
#endif`,Kf=`#ifdef USE_EMISSIVEMAP
	uniform sampler2D emissiveMap;
#endif`,jf="gl_FragColor = linearToOutputTexel( gl_FragColor );",Qf=`vec4 LinearTransferOETF( in vec4 value ) {
	return value;
}
vec4 sRGBTransferEOTF( in vec4 value ) {
	return vec4( mix( pow( value.rgb * 0.9478672986 + vec3( 0.0521327014 ), vec3( 2.4 ) ), value.rgb * 0.0773993808, vec3( lessThanEqual( value.rgb, vec3( 0.04045 ) ) ) ), value.a );
}
vec4 sRGBTransferOETF( in vec4 value ) {
	return vec4( mix( pow( value.rgb, vec3( 0.41666 ) ) * 1.055 - vec3( 0.055 ), value.rgb * 12.92, vec3( lessThanEqual( value.rgb, vec3( 0.0031308 ) ) ) ), value.a );
}`,ep=`#ifdef USE_ENVMAP
	#ifdef ENV_WORLDPOS
		vec3 cameraToFrag;
		if ( isOrthographic ) {
			cameraToFrag = normalize( vec3( - viewMatrix[ 0 ][ 2 ], - viewMatrix[ 1 ][ 2 ], - viewMatrix[ 2 ][ 2 ] ) );
		} else {
			cameraToFrag = normalize( vWorldPosition - cameraPosition );
		}
		vec3 worldNormal = inverseTransformDirection( normal, viewMatrix );
		#ifdef ENVMAP_MODE_REFLECTION
			vec3 reflectVec = reflect( cameraToFrag, worldNormal );
		#else
			vec3 reflectVec = refract( cameraToFrag, worldNormal, refractionRatio );
		#endif
	#else
		vec3 reflectVec = vReflect;
	#endif
	#ifdef ENVMAP_TYPE_CUBE
		vec4 envColor = textureCube( envMap, envMapRotation * vec3( flipEnvMap * reflectVec.x, reflectVec.yz ) );
	#else
		vec4 envColor = vec4( 0.0 );
	#endif
	#ifdef ENVMAP_BLENDING_MULTIPLY
		outgoingLight = mix( outgoingLight, outgoingLight * envColor.xyz, specularStrength * reflectivity );
	#elif defined( ENVMAP_BLENDING_MIX )
		outgoingLight = mix( outgoingLight, envColor.xyz, specularStrength * reflectivity );
	#elif defined( ENVMAP_BLENDING_ADD )
		outgoingLight += envColor.xyz * specularStrength * reflectivity;
	#endif
#endif`,tp=`#ifdef USE_ENVMAP
	uniform float envMapIntensity;
	uniform float flipEnvMap;
	uniform mat3 envMapRotation;
	#ifdef ENVMAP_TYPE_CUBE
		uniform samplerCube envMap;
	#else
		uniform sampler2D envMap;
	#endif
	
#endif`,np=`#ifdef USE_ENVMAP
	uniform float reflectivity;
	#if defined( USE_BUMPMAP ) || defined( USE_NORMALMAP ) || defined( PHONG ) || defined( LAMBERT )
		#define ENV_WORLDPOS
	#endif
	#ifdef ENV_WORLDPOS
		varying vec3 vWorldPosition;
		uniform float refractionRatio;
	#else
		varying vec3 vReflect;
	#endif
#endif`,ip=`#ifdef USE_ENVMAP
	#if defined( USE_BUMPMAP ) || defined( USE_NORMALMAP ) || defined( PHONG ) || defined( LAMBERT )
		#define ENV_WORLDPOS
	#endif
	#ifdef ENV_WORLDPOS
		
		varying vec3 vWorldPosition;
	#else
		varying vec3 vReflect;
		uniform float refractionRatio;
	#endif
#endif`,rp=`#ifdef USE_ENVMAP
	#ifdef ENV_WORLDPOS
		vWorldPosition = worldPosition.xyz;
	#else
		vec3 cameraToVertex;
		if ( isOrthographic ) {
			cameraToVertex = normalize( vec3( - viewMatrix[ 0 ][ 2 ], - viewMatrix[ 1 ][ 2 ], - viewMatrix[ 2 ][ 2 ] ) );
		} else {
			cameraToVertex = normalize( worldPosition.xyz - cameraPosition );
		}
		vec3 worldNormal = inverseTransformDirection( transformedNormal, viewMatrix );
		#ifdef ENVMAP_MODE_REFLECTION
			vReflect = reflect( cameraToVertex, worldNormal );
		#else
			vReflect = refract( cameraToVertex, worldNormal, refractionRatio );
		#endif
	#endif
#endif`,sp=`#ifdef USE_FOG
	vFogDepth = - mvPosition.z;
#endif`,ap=`#ifdef USE_FOG
	varying float vFogDepth;
#endif`,op=`#ifdef USE_FOG
	#ifdef FOG_EXP2
		float fogFactor = 1.0 - exp( - fogDensity * fogDensity * vFogDepth * vFogDepth );
	#else
		float fogFactor = smoothstep( fogNear, fogFar, vFogDepth );
	#endif
	gl_FragColor.rgb = mix( gl_FragColor.rgb, fogColor, fogFactor );
#endif`,lp=`#ifdef USE_FOG
	uniform vec3 fogColor;
	varying float vFogDepth;
	#ifdef FOG_EXP2
		uniform float fogDensity;
	#else
		uniform float fogNear;
		uniform float fogFar;
	#endif
#endif`,cp=`#ifdef USE_GRADIENTMAP
	uniform sampler2D gradientMap;
#endif
vec3 getGradientIrradiance( vec3 normal, vec3 lightDirection ) {
	float dotNL = dot( normal, lightDirection );
	vec2 coord = vec2( dotNL * 0.5 + 0.5, 0.0 );
	#ifdef USE_GRADIENTMAP
		return vec3( texture2D( gradientMap, coord ).r );
	#else
		vec2 fw = fwidth( coord ) * 0.5;
		return mix( vec3( 0.7 ), vec3( 1.0 ), smoothstep( 0.7 - fw.x, 0.7 + fw.x, coord.x ) );
	#endif
}`,dp=`#ifdef USE_LIGHTMAP
	uniform sampler2D lightMap;
	uniform float lightMapIntensity;
#endif`,up=`LambertMaterial material;
material.diffuseColor = diffuseColor.rgb;
material.specularStrength = specularStrength;`,hp=`varying vec3 vViewPosition;
struct LambertMaterial {
	vec3 diffuseColor;
	float specularStrength;
};
void RE_Direct_Lambert( const in IncidentLight directLight, const in vec3 geometryPosition, const in vec3 geometryNormal, const in vec3 geometryViewDir, const in vec3 geometryClearcoatNormal, const in LambertMaterial material, inout ReflectedLight reflectedLight ) {
	float dotNL = saturate( dot( geometryNormal, directLight.direction ) );
	vec3 irradiance = dotNL * directLight.color;
	reflectedLight.directDiffuse += irradiance * BRDF_Lambert( material.diffuseColor );
}
void RE_IndirectDiffuse_Lambert( const in vec3 irradiance, const in vec3 geometryPosition, const in vec3 geometryNormal, const in vec3 geometryViewDir, const in vec3 geometryClearcoatNormal, const in LambertMaterial material, inout ReflectedLight reflectedLight ) {
	reflectedLight.indirectDiffuse += irradiance * BRDF_Lambert( material.diffuseColor );
}
#define RE_Direct				RE_Direct_Lambert
#define RE_IndirectDiffuse		RE_IndirectDiffuse_Lambert`,fp=`uniform bool receiveShadow;
uniform vec3 ambientLightColor;
#if defined( USE_LIGHT_PROBES )
	uniform vec3 lightProbe[ 9 ];
#endif
vec3 shGetIrradianceAt( in vec3 normal, in vec3 shCoefficients[ 9 ] ) {
	float x = normal.x, y = normal.y, z = normal.z;
	vec3 result = shCoefficients[ 0 ] * 0.886227;
	result += shCoefficients[ 1 ] * 2.0 * 0.511664 * y;
	result += shCoefficients[ 2 ] * 2.0 * 0.511664 * z;
	result += shCoefficients[ 3 ] * 2.0 * 0.511664 * x;
	result += shCoefficients[ 4 ] * 2.0 * 0.429043 * x * y;
	result += shCoefficients[ 5 ] * 2.0 * 0.429043 * y * z;
	result += shCoefficients[ 6 ] * ( 0.743125 * z * z - 0.247708 );
	result += shCoefficients[ 7 ] * 2.0 * 0.429043 * x * z;
	result += shCoefficients[ 8 ] * 0.429043 * ( x * x - y * y );
	return result;
}
vec3 getLightProbeIrradiance( const in vec3 lightProbe[ 9 ], const in vec3 normal ) {
	vec3 worldNormal = inverseTransformDirection( normal, viewMatrix );
	vec3 irradiance = shGetIrradianceAt( worldNormal, lightProbe );
	return irradiance;
}
vec3 getAmbientLightIrradiance( const in vec3 ambientLightColor ) {
	vec3 irradiance = ambientLightColor;
	return irradiance;
}
float getDistanceAttenuation( const in float lightDistance, const in float cutoffDistance, const in float decayExponent ) {
	float distanceFalloff = 1.0 / max( pow( lightDistance, decayExponent ), 0.01 );
	if ( cutoffDistance > 0.0 ) {
		distanceFalloff *= pow2( saturate( 1.0 - pow4( lightDistance / cutoffDistance ) ) );
	}
	return distanceFalloff;
}
float getSpotAttenuation( const in float coneCosine, const in float penumbraCosine, const in float angleCosine ) {
	return smoothstep( coneCosine, penumbraCosine, angleCosine );
}
#if NUM_DIR_LIGHTS > 0
	struct DirectionalLight {
		vec3 direction;
		vec3 color;
	};
	uniform DirectionalLight directionalLights[ NUM_DIR_LIGHTS ];
	void getDirectionalLightInfo( const in DirectionalLight directionalLight, out IncidentLight light ) {
		light.color = directionalLight.color;
		light.direction = directionalLight.direction;
		light.visible = true;
	}
#endif
#if NUM_POINT_LIGHTS > 0
	struct PointLight {
		vec3 position;
		vec3 color;
		float distance;
		float decay;
	};
	uniform PointLight pointLights[ NUM_POINT_LIGHTS ];
	void getPointLightInfo( const in PointLight pointLight, const in vec3 geometryPosition, out IncidentLight light ) {
		vec3 lVector = pointLight.position - geometryPosition;
		light.direction = normalize( lVector );
		float lightDistance = length( lVector );
		light.color = pointLight.color;
		light.color *= getDistanceAttenuation( lightDistance, pointLight.distance, pointLight.decay );
		light.visible = ( light.color != vec3( 0.0 ) );
	}
#endif
#if NUM_SPOT_LIGHTS > 0
	struct SpotLight {
		vec3 position;
		vec3 direction;
		vec3 color;
		float distance;
		float decay;
		float coneCos;
		float penumbraCos;
	};
	uniform SpotLight spotLights[ NUM_SPOT_LIGHTS ];
	void getSpotLightInfo( const in SpotLight spotLight, const in vec3 geometryPosition, out IncidentLight light ) {
		vec3 lVector = spotLight.position - geometryPosition;
		light.direction = normalize( lVector );
		float angleCos = dot( light.direction, spotLight.direction );
		float spotAttenuation = getSpotAttenuation( spotLight.coneCos, spotLight.penumbraCos, angleCos );
		if ( spotAttenuation > 0.0 ) {
			float lightDistance = length( lVector );
			light.color = spotLight.color * spotAttenuation;
			light.color *= getDistanceAttenuation( lightDistance, spotLight.distance, spotLight.decay );
			light.visible = ( light.color != vec3( 0.0 ) );
		} else {
			light.color = vec3( 0.0 );
			light.visible = false;
		}
	}
#endif
#if NUM_RECT_AREA_LIGHTS > 0
	struct RectAreaLight {
		vec3 color;
		vec3 position;
		vec3 halfWidth;
		vec3 halfHeight;
	};
	uniform sampler2D ltc_1;	uniform sampler2D ltc_2;
	uniform RectAreaLight rectAreaLights[ NUM_RECT_AREA_LIGHTS ];
#endif
#if NUM_HEMI_LIGHTS > 0
	struct HemisphereLight {
		vec3 direction;
		vec3 skyColor;
		vec3 groundColor;
	};
	uniform HemisphereLight hemisphereLights[ NUM_HEMI_LIGHTS ];
	vec3 getHemisphereLightIrradiance( const in HemisphereLight hemiLight, const in vec3 normal ) {
		float dotNL = dot( normal, hemiLight.direction );
		float hemiDiffuseWeight = 0.5 * dotNL + 0.5;
		vec3 irradiance = mix( hemiLight.groundColor, hemiLight.skyColor, hemiDiffuseWeight );
		return irradiance;
	}
#endif`,pp=`#ifdef USE_ENVMAP
	vec3 getIBLIrradiance( const in vec3 normal ) {
		#ifdef ENVMAP_TYPE_CUBE_UV
			vec3 worldNormal = inverseTransformDirection( normal, viewMatrix );
			vec4 envMapColor = textureCubeUV( envMap, envMapRotation * worldNormal, 1.0 );
			return PI * envMapColor.rgb * envMapIntensity;
		#else
			return vec3( 0.0 );
		#endif
	}
	vec3 getIBLRadiance( const in vec3 viewDir, const in vec3 normal, const in float roughness ) {
		#ifdef ENVMAP_TYPE_CUBE_UV
			vec3 reflectVec = reflect( - viewDir, normal );
			reflectVec = normalize( mix( reflectVec, normal, roughness * roughness) );
			reflectVec = inverseTransformDirection( reflectVec, viewMatrix );
			vec4 envMapColor = textureCubeUV( envMap, envMapRotation * reflectVec, roughness );
			return envMapColor.rgb * envMapIntensity;
		#else
			return vec3( 0.0 );
		#endif
	}
	#ifdef USE_ANISOTROPY
		vec3 getIBLAnisotropyRadiance( const in vec3 viewDir, const in vec3 normal, const in float roughness, const in vec3 bitangent, const in float anisotropy ) {
			#ifdef ENVMAP_TYPE_CUBE_UV
				vec3 bentNormal = cross( bitangent, viewDir );
				bentNormal = normalize( cross( bentNormal, bitangent ) );
				bentNormal = normalize( mix( bentNormal, normal, pow2( pow2( 1.0 - anisotropy * ( 1.0 - roughness ) ) ) ) );
				return getIBLRadiance( viewDir, bentNormal, roughness );
			#else
				return vec3( 0.0 );
			#endif
		}
	#endif
#endif`,mp=`ToonMaterial material;
material.diffuseColor = diffuseColor.rgb;`,gp=`varying vec3 vViewPosition;
struct ToonMaterial {
	vec3 diffuseColor;
};
void RE_Direct_Toon( const in IncidentLight directLight, const in vec3 geometryPosition, const in vec3 geometryNormal, const in vec3 geometryViewDir, const in vec3 geometryClearcoatNormal, const in ToonMaterial material, inout ReflectedLight reflectedLight ) {
	vec3 irradiance = getGradientIrradiance( geometryNormal, directLight.direction ) * directLight.color;
	reflectedLight.directDiffuse += irradiance * BRDF_Lambert( material.diffuseColor );
}
void RE_IndirectDiffuse_Toon( const in vec3 irradiance, const in vec3 geometryPosition, const in vec3 geometryNormal, const in vec3 geometryViewDir, const in vec3 geometryClearcoatNormal, const in ToonMaterial material, inout ReflectedLight reflectedLight ) {
	reflectedLight.indirectDiffuse += irradiance * BRDF_Lambert( material.diffuseColor );
}
#define RE_Direct				RE_Direct_Toon
#define RE_IndirectDiffuse		RE_IndirectDiffuse_Toon`,xp=`BlinnPhongMaterial material;
material.diffuseColor = diffuseColor.rgb;
material.specularColor = specular;
material.specularShininess = shininess;
material.specularStrength = specularStrength;`,_p=`varying vec3 vViewPosition;
struct BlinnPhongMaterial {
	vec3 diffuseColor;
	vec3 specularColor;
	float specularShininess;
	float specularStrength;
};
void RE_Direct_BlinnPhong( const in IncidentLight directLight, const in vec3 geometryPosition, const in vec3 geometryNormal, const in vec3 geometryViewDir, const in vec3 geometryClearcoatNormal, const in BlinnPhongMaterial material, inout ReflectedLight reflectedLight ) {
	float dotNL = saturate( dot( geometryNormal, directLight.direction ) );
	vec3 irradiance = dotNL * directLight.color;
	reflectedLight.directDiffuse += irradiance * BRDF_Lambert( material.diffuseColor );
	reflectedLight.directSpecular += irradiance * BRDF_BlinnPhong( directLight.direction, geometryViewDir, geometryNormal, material.specularColor, material.specularShininess ) * material.specularStrength;
}
void RE_IndirectDiffuse_BlinnPhong( const in vec3 irradiance, const in vec3 geometryPosition, const in vec3 geometryNormal, const in vec3 geometryViewDir, const in vec3 geometryClearcoatNormal, const in BlinnPhongMaterial material, inout ReflectedLight reflectedLight ) {
	reflectedLight.indirectDiffuse += irradiance * BRDF_Lambert( material.diffuseColor );
}
#define RE_Direct				RE_Direct_BlinnPhong
#define RE_IndirectDiffuse		RE_IndirectDiffuse_BlinnPhong`,yp=`PhysicalMaterial material;
material.diffuseColor = diffuseColor.rgb * ( 1.0 - metalnessFactor );
vec3 dxy = max( abs( dFdx( nonPerturbedNormal ) ), abs( dFdy( nonPerturbedNormal ) ) );
float geometryRoughness = max( max( dxy.x, dxy.y ), dxy.z );
material.roughness = max( roughnessFactor, 0.0525 );material.roughness += geometryRoughness;
material.roughness = min( material.roughness, 1.0 );
#ifdef IOR
	material.ior = ior;
	#ifdef USE_SPECULAR
		float specularIntensityFactor = specularIntensity;
		vec3 specularColorFactor = specularColor;
		#ifdef USE_SPECULAR_COLORMAP
			specularColorFactor *= texture2D( specularColorMap, vSpecularColorMapUv ).rgb;
		#endif
		#ifdef USE_SPECULAR_INTENSITYMAP
			specularIntensityFactor *= texture2D( specularIntensityMap, vSpecularIntensityMapUv ).a;
		#endif
		material.specularF90 = mix( specularIntensityFactor, 1.0, metalnessFactor );
	#else
		float specularIntensityFactor = 1.0;
		vec3 specularColorFactor = vec3( 1.0 );
		material.specularF90 = 1.0;
	#endif
	material.specularColor = mix( min( pow2( ( material.ior - 1.0 ) / ( material.ior + 1.0 ) ) * specularColorFactor, vec3( 1.0 ) ) * specularIntensityFactor, diffuseColor.rgb, metalnessFactor );
#else
	material.specularColor = mix( vec3( 0.04 ), diffuseColor.rgb, metalnessFactor );
	material.specularF90 = 1.0;
#endif
#ifdef USE_CLEARCOAT
	material.clearcoat = clearcoat;
	material.clearcoatRoughness = clearcoatRoughness;
	material.clearcoatF0 = vec3( 0.04 );
	material.clearcoatF90 = 1.0;
	#ifdef USE_CLEARCOATMAP
		material.clearcoat *= texture2D( clearcoatMap, vClearcoatMapUv ).x;
	#endif
	#ifdef USE_CLEARCOAT_ROUGHNESSMAP
		material.clearcoatRoughness *= texture2D( clearcoatRoughnessMap, vClearcoatRoughnessMapUv ).y;
	#endif
	material.clearcoat = saturate( material.clearcoat );	material.clearcoatRoughness = max( material.clearcoatRoughness, 0.0525 );
	material.clearcoatRoughness += geometryRoughness;
	material.clearcoatRoughness = min( material.clearcoatRoughness, 1.0 );
#endif
#ifdef USE_DISPERSION
	material.dispersion = dispersion;
#endif
#ifdef USE_IRIDESCENCE
	material.iridescence = iridescence;
	material.iridescenceIOR = iridescenceIOR;
	#ifdef USE_IRIDESCENCEMAP
		material.iridescence *= texture2D( iridescenceMap, vIridescenceMapUv ).r;
	#endif
	#ifdef USE_IRIDESCENCE_THICKNESSMAP
		material.iridescenceThickness = (iridescenceThicknessMaximum - iridescenceThicknessMinimum) * texture2D( iridescenceThicknessMap, vIridescenceThicknessMapUv ).g + iridescenceThicknessMinimum;
	#else
		material.iridescenceThickness = iridescenceThicknessMaximum;
	#endif
#endif
#ifdef USE_SHEEN
	material.sheenColor = sheenColor;
	#ifdef USE_SHEEN_COLORMAP
		material.sheenColor *= texture2D( sheenColorMap, vSheenColorMapUv ).rgb;
	#endif
	material.sheenRoughness = clamp( sheenRoughness, 0.07, 1.0 );
	#ifdef USE_SHEEN_ROUGHNESSMAP
		material.sheenRoughness *= texture2D( sheenRoughnessMap, vSheenRoughnessMapUv ).a;
	#endif
#endif
#ifdef USE_ANISOTROPY
	#ifdef USE_ANISOTROPYMAP
		mat2 anisotropyMat = mat2( anisotropyVector.x, anisotropyVector.y, - anisotropyVector.y, anisotropyVector.x );
		vec3 anisotropyPolar = texture2D( anisotropyMap, vAnisotropyMapUv ).rgb;
		vec2 anisotropyV = anisotropyMat * normalize( 2.0 * anisotropyPolar.rg - vec2( 1.0 ) ) * anisotropyPolar.b;
	#else
		vec2 anisotropyV = anisotropyVector;
	#endif
	material.anisotropy = length( anisotropyV );
	if( material.anisotropy == 0.0 ) {
		anisotropyV = vec2( 1.0, 0.0 );
	} else {
		anisotropyV /= material.anisotropy;
		material.anisotropy = saturate( material.anisotropy );
	}
	material.alphaT = mix( pow2( material.roughness ), 1.0, pow2( material.anisotropy ) );
	material.anisotropyT = tbn[ 0 ] * anisotropyV.x + tbn[ 1 ] * anisotropyV.y;
	material.anisotropyB = tbn[ 1 ] * anisotropyV.x - tbn[ 0 ] * anisotropyV.y;
#endif`,vp=`struct PhysicalMaterial {
	vec3 diffuseColor;
	float roughness;
	vec3 specularColor;
	float specularF90;
	float dispersion;
	#ifdef USE_CLEARCOAT
		float clearcoat;
		float clearcoatRoughness;
		vec3 clearcoatF0;
		float clearcoatF90;
	#endif
	#ifdef USE_IRIDESCENCE
		float iridescence;
		float iridescenceIOR;
		float iridescenceThickness;
		vec3 iridescenceFresnel;
		vec3 iridescenceF0;
	#endif
	#ifdef USE_SHEEN
		vec3 sheenColor;
		float sheenRoughness;
	#endif
	#ifdef IOR
		float ior;
	#endif
	#ifdef USE_TRANSMISSION
		float transmission;
		float transmissionAlpha;
		float thickness;
		float attenuationDistance;
		vec3 attenuationColor;
	#endif
	#ifdef USE_ANISOTROPY
		float anisotropy;
		float alphaT;
		vec3 anisotropyT;
		vec3 anisotropyB;
	#endif
};
vec3 clearcoatSpecularDirect = vec3( 0.0 );
vec3 clearcoatSpecularIndirect = vec3( 0.0 );
vec3 sheenSpecularDirect = vec3( 0.0 );
vec3 sheenSpecularIndirect = vec3(0.0 );
vec3 Schlick_to_F0( const in vec3 f, const in float f90, const in float dotVH ) {
    float x = clamp( 1.0 - dotVH, 0.0, 1.0 );
    float x2 = x * x;
    float x5 = clamp( x * x2 * x2, 0.0, 0.9999 );
    return ( f - vec3( f90 ) * x5 ) / ( 1.0 - x5 );
}
float V_GGX_SmithCorrelated( const in float alpha, const in float dotNL, const in float dotNV ) {
	float a2 = pow2( alpha );
	float gv = dotNL * sqrt( a2 + ( 1.0 - a2 ) * pow2( dotNV ) );
	float gl = dotNV * sqrt( a2 + ( 1.0 - a2 ) * pow2( dotNL ) );
	return 0.5 / max( gv + gl, EPSILON );
}
float D_GGX( const in float alpha, const in float dotNH ) {
	float a2 = pow2( alpha );
	float denom = pow2( dotNH ) * ( a2 - 1.0 ) + 1.0;
	return RECIPROCAL_PI * a2 / pow2( denom );
}
#ifdef USE_ANISOTROPY
	float V_GGX_SmithCorrelated_Anisotropic( const in float alphaT, const in float alphaB, const in float dotTV, const in float dotBV, const in float dotTL, const in float dotBL, const in float dotNV, const in float dotNL ) {
		float gv = dotNL * length( vec3( alphaT * dotTV, alphaB * dotBV, dotNV ) );
		float gl = dotNV * length( vec3( alphaT * dotTL, alphaB * dotBL, dotNL ) );
		float v = 0.5 / ( gv + gl );
		return saturate(v);
	}
	float D_GGX_Anisotropic( const in float alphaT, const in float alphaB, const in float dotNH, const in float dotTH, const in float dotBH ) {
		float a2 = alphaT * alphaB;
		highp vec3 v = vec3( alphaB * dotTH, alphaT * dotBH, a2 * dotNH );
		highp float v2 = dot( v, v );
		float w2 = a2 / v2;
		return RECIPROCAL_PI * a2 * pow2 ( w2 );
	}
#endif
#ifdef USE_CLEARCOAT
	vec3 BRDF_GGX_Clearcoat( const in vec3 lightDir, const in vec3 viewDir, const in vec3 normal, const in PhysicalMaterial material) {
		vec3 f0 = material.clearcoatF0;
		float f90 = material.clearcoatF90;
		float roughness = material.clearcoatRoughness;
		float alpha = pow2( roughness );
		vec3 halfDir = normalize( lightDir + viewDir );
		float dotNL = saturate( dot( normal, lightDir ) );
		float dotNV = saturate( dot( normal, viewDir ) );
		float dotNH = saturate( dot( normal, halfDir ) );
		float dotVH = saturate( dot( viewDir, halfDir ) );
		vec3 F = F_Schlick( f0, f90, dotVH );
		float V = V_GGX_SmithCorrelated( alpha, dotNL, dotNV );
		float D = D_GGX( alpha, dotNH );
		return F * ( V * D );
	}
#endif
vec3 BRDF_GGX( const in vec3 lightDir, const in vec3 viewDir, const in vec3 normal, const in PhysicalMaterial material ) {
	vec3 f0 = material.specularColor;
	float f90 = material.specularF90;
	float roughness = material.roughness;
	float alpha = pow2( roughness );
	vec3 halfDir = normalize( lightDir + viewDir );
	float dotNL = saturate( dot( normal, lightDir ) );
	float dotNV = saturate( dot( normal, viewDir ) );
	float dotNH = saturate( dot( normal, halfDir ) );
	float dotVH = saturate( dot( viewDir, halfDir ) );
	vec3 F = F_Schlick( f0, f90, dotVH );
	#ifdef USE_IRIDESCENCE
		F = mix( F, material.iridescenceFresnel, material.iridescence );
	#endif
	#ifdef USE_ANISOTROPY
		float dotTL = dot( material.anisotropyT, lightDir );
		float dotTV = dot( material.anisotropyT, viewDir );
		float dotTH = dot( material.anisotropyT, halfDir );
		float dotBL = dot( material.anisotropyB, lightDir );
		float dotBV = dot( material.anisotropyB, viewDir );
		float dotBH = dot( material.anisotropyB, halfDir );
		float V = V_GGX_SmithCorrelated_Anisotropic( material.alphaT, alpha, dotTV, dotBV, dotTL, dotBL, dotNV, dotNL );
		float D = D_GGX_Anisotropic( material.alphaT, alpha, dotNH, dotTH, dotBH );
	#else
		float V = V_GGX_SmithCorrelated( alpha, dotNL, dotNV );
		float D = D_GGX( alpha, dotNH );
	#endif
	return F * ( V * D );
}
vec2 LTC_Uv( const in vec3 N, const in vec3 V, const in float roughness ) {
	const float LUT_SIZE = 64.0;
	const float LUT_SCALE = ( LUT_SIZE - 1.0 ) / LUT_SIZE;
	const float LUT_BIAS = 0.5 / LUT_SIZE;
	float dotNV = saturate( dot( N, V ) );
	vec2 uv = vec2( roughness, sqrt( 1.0 - dotNV ) );
	uv = uv * LUT_SCALE + LUT_BIAS;
	return uv;
}
float LTC_ClippedSphereFormFactor( const in vec3 f ) {
	float l = length( f );
	return max( ( l * l + f.z ) / ( l + 1.0 ), 0.0 );
}
vec3 LTC_EdgeVectorFormFactor( const in vec3 v1, const in vec3 v2 ) {
	float x = dot( v1, v2 );
	float y = abs( x );
	float a = 0.8543985 + ( 0.4965155 + 0.0145206 * y ) * y;
	float b = 3.4175940 + ( 4.1616724 + y ) * y;
	float v = a / b;
	float theta_sintheta = ( x > 0.0 ) ? v : 0.5 * inversesqrt( max( 1.0 - x * x, 1e-7 ) ) - v;
	return cross( v1, v2 ) * theta_sintheta;
}
vec3 LTC_Evaluate( const in vec3 N, const in vec3 V, const in vec3 P, const in mat3 mInv, const in vec3 rectCoords[ 4 ] ) {
	vec3 v1 = rectCoords[ 1 ] - rectCoords[ 0 ];
	vec3 v2 = rectCoords[ 3 ] - rectCoords[ 0 ];
	vec3 lightNormal = cross( v1, v2 );
	if( dot( lightNormal, P - rectCoords[ 0 ] ) < 0.0 ) return vec3( 0.0 );
	vec3 T1, T2;
	T1 = normalize( V - N * dot( V, N ) );
	T2 = - cross( N, T1 );
	mat3 mat = mInv * transposeMat3( mat3( T1, T2, N ) );
	vec3 coords[ 4 ];
	coords[ 0 ] = mat * ( rectCoords[ 0 ] - P );
	coords[ 1 ] = mat * ( rectCoords[ 1 ] - P );
	coords[ 2 ] = mat * ( rectCoords[ 2 ] - P );
	coords[ 3 ] = mat * ( rectCoords[ 3 ] - P );
	coords[ 0 ] = normalize( coords[ 0 ] );
	coords[ 1 ] = normalize( coords[ 1 ] );
	coords[ 2 ] = normalize( coords[ 2 ] );
	coords[ 3 ] = normalize( coords[ 3 ] );
	vec3 vectorFormFactor = vec3( 0.0 );
	vectorFormFactor += LTC_EdgeVectorFormFactor( coords[ 0 ], coords[ 1 ] );
	vectorFormFactor += LTC_EdgeVectorFormFactor( coords[ 1 ], coords[ 2 ] );
	vectorFormFactor += LTC_EdgeVectorFormFactor( coords[ 2 ], coords[ 3 ] );
	vectorFormFactor += LTC_EdgeVectorFormFactor( coords[ 3 ], coords[ 0 ] );
	float result = LTC_ClippedSphereFormFactor( vectorFormFactor );
	return vec3( result );
}
#if defined( USE_SHEEN )
float D_Charlie( float roughness, float dotNH ) {
	float alpha = pow2( roughness );
	float invAlpha = 1.0 / alpha;
	float cos2h = dotNH * dotNH;
	float sin2h = max( 1.0 - cos2h, 0.0078125 );
	return ( 2.0 + invAlpha ) * pow( sin2h, invAlpha * 0.5 ) / ( 2.0 * PI );
}
float V_Neubelt( float dotNV, float dotNL ) {
	return saturate( 1.0 / ( 4.0 * ( dotNL + dotNV - dotNL * dotNV ) ) );
}
vec3 BRDF_Sheen( const in vec3 lightDir, const in vec3 viewDir, const in vec3 normal, vec3 sheenColor, const in float sheenRoughness ) {
	vec3 halfDir = normalize( lightDir + viewDir );
	float dotNL = saturate( dot( normal, lightDir ) );
	float dotNV = saturate( dot( normal, viewDir ) );
	float dotNH = saturate( dot( normal, halfDir ) );
	float D = D_Charlie( sheenRoughness, dotNH );
	float V = V_Neubelt( dotNV, dotNL );
	return sheenColor * ( D * V );
}
#endif
float IBLSheenBRDF( const in vec3 normal, const in vec3 viewDir, const in float roughness ) {
	float dotNV = saturate( dot( normal, viewDir ) );
	float r2 = roughness * roughness;
	float a = roughness < 0.25 ? -339.2 * r2 + 161.4 * roughness - 25.9 : -8.48 * r2 + 14.3 * roughness - 9.95;
	float b = roughness < 0.25 ? 44.0 * r2 - 23.7 * roughness + 3.26 : 1.97 * r2 - 3.27 * roughness + 0.72;
	float DG = exp( a * dotNV + b ) + ( roughness < 0.25 ? 0.0 : 0.1 * ( roughness - 0.25 ) );
	return saturate( DG * RECIPROCAL_PI );
}
vec2 DFGApprox( const in vec3 normal, const in vec3 viewDir, const in float roughness ) {
	float dotNV = saturate( dot( normal, viewDir ) );
	const vec4 c0 = vec4( - 1, - 0.0275, - 0.572, 0.022 );
	const vec4 c1 = vec4( 1, 0.0425, 1.04, - 0.04 );
	vec4 r = roughness * c0 + c1;
	float a004 = min( r.x * r.x, exp2( - 9.28 * dotNV ) ) * r.x + r.y;
	vec2 fab = vec2( - 1.04, 1.04 ) * a004 + r.zw;
	return fab;
}
vec3 EnvironmentBRDF( const in vec3 normal, const in vec3 viewDir, const in vec3 specularColor, const in float specularF90, const in float roughness ) {
	vec2 fab = DFGApprox( normal, viewDir, roughness );
	return specularColor * fab.x + specularF90 * fab.y;
}
#ifdef USE_IRIDESCENCE
void computeMultiscatteringIridescence( const in vec3 normal, const in vec3 viewDir, const in vec3 specularColor, const in float specularF90, const in float iridescence, const in vec3 iridescenceF0, const in float roughness, inout vec3 singleScatter, inout vec3 multiScatter ) {
#else
void computeMultiscattering( const in vec3 normal, const in vec3 viewDir, const in vec3 specularColor, const in float specularF90, const in float roughness, inout vec3 singleScatter, inout vec3 multiScatter ) {
#endif
	vec2 fab = DFGApprox( normal, viewDir, roughness );
	#ifdef USE_IRIDESCENCE
		vec3 Fr = mix( specularColor, iridescenceF0, iridescence );
	#else
		vec3 Fr = specularColor;
	#endif
	vec3 FssEss = Fr * fab.x + specularF90 * fab.y;
	float Ess = fab.x + fab.y;
	float Ems = 1.0 - Ess;
	vec3 Favg = Fr + ( 1.0 - Fr ) * 0.047619;	vec3 Fms = FssEss * Favg / ( 1.0 - Ems * Favg );
	singleScatter += FssEss;
	multiScatter += Fms * Ems;
}
#if NUM_RECT_AREA_LIGHTS > 0
	void RE_Direct_RectArea_Physical( const in RectAreaLight rectAreaLight, const in vec3 geometryPosition, const in vec3 geometryNormal, const in vec3 geometryViewDir, const in vec3 geometryClearcoatNormal, const in PhysicalMaterial material, inout ReflectedLight reflectedLight ) {
		vec3 normal = geometryNormal;
		vec3 viewDir = geometryViewDir;
		vec3 position = geometryPosition;
		vec3 lightPos = rectAreaLight.position;
		vec3 halfWidth = rectAreaLight.halfWidth;
		vec3 halfHeight = rectAreaLight.halfHeight;
		vec3 lightColor = rectAreaLight.color;
		float roughness = material.roughness;
		vec3 rectCoords[ 4 ];
		rectCoords[ 0 ] = lightPos + halfWidth - halfHeight;		rectCoords[ 1 ] = lightPos - halfWidth - halfHeight;
		rectCoords[ 2 ] = lightPos - halfWidth + halfHeight;
		rectCoords[ 3 ] = lightPos + halfWidth + halfHeight;
		vec2 uv = LTC_Uv( normal, viewDir, roughness );
		vec4 t1 = texture2D( ltc_1, uv );
		vec4 t2 = texture2D( ltc_2, uv );
		mat3 mInv = mat3(
			vec3( t1.x, 0, t1.y ),
			vec3(    0, 1,    0 ),
			vec3( t1.z, 0, t1.w )
		);
		vec3 fresnel = ( material.specularColor * t2.x + ( vec3( 1.0 ) - material.specularColor ) * t2.y );
		reflectedLight.directSpecular += lightColor * fresnel * LTC_Evaluate( normal, viewDir, position, mInv, rectCoords );
		reflectedLight.directDiffuse += lightColor * material.diffuseColor * LTC_Evaluate( normal, viewDir, position, mat3( 1.0 ), rectCoords );
	}
#endif
void RE_Direct_Physical( const in IncidentLight directLight, const in vec3 geometryPosition, const in vec3 geometryNormal, const in vec3 geometryViewDir, const in vec3 geometryClearcoatNormal, const in PhysicalMaterial material, inout ReflectedLight reflectedLight ) {
	float dotNL = saturate( dot( geometryNormal, directLight.direction ) );
	vec3 irradiance = dotNL * directLight.color;
	#ifdef USE_CLEARCOAT
		float dotNLcc = saturate( dot( geometryClearcoatNormal, directLight.direction ) );
		vec3 ccIrradiance = dotNLcc * directLight.color;
		clearcoatSpecularDirect += ccIrradiance * BRDF_GGX_Clearcoat( directLight.direction, geometryViewDir, geometryClearcoatNormal, material );
	#endif
	#ifdef USE_SHEEN
		sheenSpecularDirect += irradiance * BRDF_Sheen( directLight.direction, geometryViewDir, geometryNormal, material.sheenColor, material.sheenRoughness );
	#endif
	reflectedLight.directSpecular += irradiance * BRDF_GGX( directLight.direction, geometryViewDir, geometryNormal, material );
	reflectedLight.directDiffuse += irradiance * BRDF_Lambert( material.diffuseColor );
}
void RE_IndirectDiffuse_Physical( const in vec3 irradiance, const in vec3 geometryPosition, const in vec3 geometryNormal, const in vec3 geometryViewDir, const in vec3 geometryClearcoatNormal, const in PhysicalMaterial material, inout ReflectedLight reflectedLight ) {
	reflectedLight.indirectDiffuse += irradiance * BRDF_Lambert( material.diffuseColor );
}
void RE_IndirectSpecular_Physical( const in vec3 radiance, const in vec3 irradiance, const in vec3 clearcoatRadiance, const in vec3 geometryPosition, const in vec3 geometryNormal, const in vec3 geometryViewDir, const in vec3 geometryClearcoatNormal, const in PhysicalMaterial material, inout ReflectedLight reflectedLight) {
	#ifdef USE_CLEARCOAT
		clearcoatSpecularIndirect += clearcoatRadiance * EnvironmentBRDF( geometryClearcoatNormal, geometryViewDir, material.clearcoatF0, material.clearcoatF90, material.clearcoatRoughness );
	#endif
	#ifdef USE_SHEEN
		sheenSpecularIndirect += irradiance * material.sheenColor * IBLSheenBRDF( geometryNormal, geometryViewDir, material.sheenRoughness );
	#endif
	vec3 singleScattering = vec3( 0.0 );
	vec3 multiScattering = vec3( 0.0 );
	vec3 cosineWeightedIrradiance = irradiance * RECIPROCAL_PI;
	#ifdef USE_IRIDESCENCE
		computeMultiscatteringIridescence( geometryNormal, geometryViewDir, material.specularColor, material.specularF90, material.iridescence, material.iridescenceFresnel, material.roughness, singleScattering, multiScattering );
	#else
		computeMultiscattering( geometryNormal, geometryViewDir, material.specularColor, material.specularF90, material.roughness, singleScattering, multiScattering );
	#endif
	vec3 totalScattering = singleScattering + multiScattering;
	vec3 diffuse = material.diffuseColor * ( 1.0 - max( max( totalScattering.r, totalScattering.g ), totalScattering.b ) );
	reflectedLight.indirectSpecular += radiance * singleScattering;
	reflectedLight.indirectSpecular += multiScattering * cosineWeightedIrradiance;
	reflectedLight.indirectDiffuse += diffuse * cosineWeightedIrradiance;
}
#define RE_Direct				RE_Direct_Physical
#define RE_Direct_RectArea		RE_Direct_RectArea_Physical
#define RE_IndirectDiffuse		RE_IndirectDiffuse_Physical
#define RE_IndirectSpecular		RE_IndirectSpecular_Physical
float computeSpecularOcclusion( const in float dotNV, const in float ambientOcclusion, const in float roughness ) {
	return saturate( pow( dotNV + ambientOcclusion, exp2( - 16.0 * roughness - 1.0 ) ) - 1.0 + ambientOcclusion );
}`,bp=`
vec3 geometryPosition = - vViewPosition;
vec3 geometryNormal = normal;
vec3 geometryViewDir = ( isOrthographic ) ? vec3( 0, 0, 1 ) : normalize( vViewPosition );
vec3 geometryClearcoatNormal = vec3( 0.0 );
#ifdef USE_CLEARCOAT
	geometryClearcoatNormal = clearcoatNormal;
#endif
#ifdef USE_IRIDESCENCE
	float dotNVi = saturate( dot( normal, geometryViewDir ) );
	if ( material.iridescenceThickness == 0.0 ) {
		material.iridescence = 0.0;
	} else {
		material.iridescence = saturate( material.iridescence );
	}
	if ( material.iridescence > 0.0 ) {
		material.iridescenceFresnel = evalIridescence( 1.0, material.iridescenceIOR, dotNVi, material.iridescenceThickness, material.specularColor );
		material.iridescenceF0 = Schlick_to_F0( material.iridescenceFresnel, 1.0, dotNVi );
	}
#endif
IncidentLight directLight;
#if ( NUM_POINT_LIGHTS > 0 ) && defined( RE_Direct )
	PointLight pointLight;
	#if defined( USE_SHADOWMAP ) && NUM_POINT_LIGHT_SHADOWS > 0
	PointLightShadow pointLightShadow;
	#endif
	#pragma unroll_loop_start
	for ( int i = 0; i < NUM_POINT_LIGHTS; i ++ ) {
		pointLight = pointLights[ i ];
		getPointLightInfo( pointLight, geometryPosition, directLight );
		#if defined( USE_SHADOWMAP ) && ( UNROLLED_LOOP_INDEX < NUM_POINT_LIGHT_SHADOWS )
		pointLightShadow = pointLightShadows[ i ];
		directLight.color *= ( directLight.visible && receiveShadow ) ? getPointShadow( pointShadowMap[ i ], pointLightShadow.shadowMapSize, pointLightShadow.shadowIntensity, pointLightShadow.shadowBias, pointLightShadow.shadowRadius, vPointShadowCoord[ i ], pointLightShadow.shadowCameraNear, pointLightShadow.shadowCameraFar ) : 1.0;
		#endif
		RE_Direct( directLight, geometryPosition, geometryNormal, geometryViewDir, geometryClearcoatNormal, material, reflectedLight );
	}
	#pragma unroll_loop_end
#endif
#if ( NUM_SPOT_LIGHTS > 0 ) && defined( RE_Direct )
	SpotLight spotLight;
	vec4 spotColor;
	vec3 spotLightCoord;
	bool inSpotLightMap;
	#if defined( USE_SHADOWMAP ) && NUM_SPOT_LIGHT_SHADOWS > 0
	SpotLightShadow spotLightShadow;
	#endif
	#pragma unroll_loop_start
	for ( int i = 0; i < NUM_SPOT_LIGHTS; i ++ ) {
		spotLight = spotLights[ i ];
		getSpotLightInfo( spotLight, geometryPosition, directLight );
		#if ( UNROLLED_LOOP_INDEX < NUM_SPOT_LIGHT_SHADOWS_WITH_MAPS )
		#define SPOT_LIGHT_MAP_INDEX UNROLLED_LOOP_INDEX
		#elif ( UNROLLED_LOOP_INDEX < NUM_SPOT_LIGHT_SHADOWS )
		#define SPOT_LIGHT_MAP_INDEX NUM_SPOT_LIGHT_MAPS
		#else
		#define SPOT_LIGHT_MAP_INDEX ( UNROLLED_LOOP_INDEX - NUM_SPOT_LIGHT_SHADOWS + NUM_SPOT_LIGHT_SHADOWS_WITH_MAPS )
		#endif
		#if ( SPOT_LIGHT_MAP_INDEX < NUM_SPOT_LIGHT_MAPS )
			spotLightCoord = vSpotLightCoord[ i ].xyz / vSpotLightCoord[ i ].w;
			inSpotLightMap = all( lessThan( abs( spotLightCoord * 2. - 1. ), vec3( 1.0 ) ) );
			spotColor = texture2D( spotLightMap[ SPOT_LIGHT_MAP_INDEX ], spotLightCoord.xy );
			directLight.color = inSpotLightMap ? directLight.color * spotColor.rgb : directLight.color;
		#endif
		#undef SPOT_LIGHT_MAP_INDEX
		#if defined( USE_SHADOWMAP ) && ( UNROLLED_LOOP_INDEX < NUM_SPOT_LIGHT_SHADOWS )
		spotLightShadow = spotLightShadows[ i ];
		directLight.color *= ( directLight.visible && receiveShadow ) ? getShadow( spotShadowMap[ i ], spotLightShadow.shadowMapSize, spotLightShadow.shadowIntensity, spotLightShadow.shadowBias, spotLightShadow.shadowRadius, vSpotLightCoord[ i ] ) : 1.0;
		#endif
		RE_Direct( directLight, geometryPosition, geometryNormal, geometryViewDir, geometryClearcoatNormal, material, reflectedLight );
	}
	#pragma unroll_loop_end
#endif
#if ( NUM_DIR_LIGHTS > 0 ) && defined( RE_Direct )
	DirectionalLight directionalLight;
	#if defined( USE_SHADOWMAP ) && NUM_DIR_LIGHT_SHADOWS > 0
	DirectionalLightShadow directionalLightShadow;
	#endif
	#pragma unroll_loop_start
	for ( int i = 0; i < NUM_DIR_LIGHTS; i ++ ) {
		directionalLight = directionalLights[ i ];
		getDirectionalLightInfo( directionalLight, directLight );
		#if defined( USE_SHADOWMAP ) && ( UNROLLED_LOOP_INDEX < NUM_DIR_LIGHT_SHADOWS )
		directionalLightShadow = directionalLightShadows[ i ];
		directLight.color *= ( directLight.visible && receiveShadow ) ? getShadow( directionalShadowMap[ i ], directionalLightShadow.shadowMapSize, directionalLightShadow.shadowIntensity, directionalLightShadow.shadowBias, directionalLightShadow.shadowRadius, vDirectionalShadowCoord[ i ] ) : 1.0;
		#endif
		RE_Direct( directLight, geometryPosition, geometryNormal, geometryViewDir, geometryClearcoatNormal, material, reflectedLight );
	}
	#pragma unroll_loop_end
#endif
#if ( NUM_RECT_AREA_LIGHTS > 0 ) && defined( RE_Direct_RectArea )
	RectAreaLight rectAreaLight;
	#pragma unroll_loop_start
	for ( int i = 0; i < NUM_RECT_AREA_LIGHTS; i ++ ) {
		rectAreaLight = rectAreaLights[ i ];
		RE_Direct_RectArea( rectAreaLight, geometryPosition, geometryNormal, geometryViewDir, geometryClearcoatNormal, material, reflectedLight );
	}
	#pragma unroll_loop_end
#endif
#if defined( RE_IndirectDiffuse )
	vec3 iblIrradiance = vec3( 0.0 );
	vec3 irradiance = getAmbientLightIrradiance( ambientLightColor );
	#if defined( USE_LIGHT_PROBES )
		irradiance += getLightProbeIrradiance( lightProbe, geometryNormal );
	#endif
	#if ( NUM_HEMI_LIGHTS > 0 )
		#pragma unroll_loop_start
		for ( int i = 0; i < NUM_HEMI_LIGHTS; i ++ ) {
			irradiance += getHemisphereLightIrradiance( hemisphereLights[ i ], geometryNormal );
		}
		#pragma unroll_loop_end
	#endif
#endif
#if defined( RE_IndirectSpecular )
	vec3 radiance = vec3( 0.0 );
	vec3 clearcoatRadiance = vec3( 0.0 );
#endif`,wp=`#if defined( RE_IndirectDiffuse )
	#ifdef USE_LIGHTMAP
		vec4 lightMapTexel = texture2D( lightMap, vLightMapUv );
		vec3 lightMapIrradiance = lightMapTexel.rgb * lightMapIntensity;
		irradiance += lightMapIrradiance;
	#endif
	#if defined( USE_ENVMAP ) && defined( STANDARD ) && defined( ENVMAP_TYPE_CUBE_UV )
		iblIrradiance += getIBLIrradiance( geometryNormal );
	#endif
#endif
#if defined( USE_ENVMAP ) && defined( RE_IndirectSpecular )
	#ifdef USE_ANISOTROPY
		radiance += getIBLAnisotropyRadiance( geometryViewDir, geometryNormal, material.roughness, material.anisotropyB, material.anisotropy );
	#else
		radiance += getIBLRadiance( geometryViewDir, geometryNormal, material.roughness );
	#endif
	#ifdef USE_CLEARCOAT
		clearcoatRadiance += getIBLRadiance( geometryViewDir, geometryClearcoatNormal, material.clearcoatRoughness );
	#endif
#endif`,Mp=`#if defined( RE_IndirectDiffuse )
	RE_IndirectDiffuse( irradiance, geometryPosition, geometryNormal, geometryViewDir, geometryClearcoatNormal, material, reflectedLight );
#endif
#if defined( RE_IndirectSpecular )
	RE_IndirectSpecular( radiance, iblIrradiance, clearcoatRadiance, geometryPosition, geometryNormal, geometryViewDir, geometryClearcoatNormal, material, reflectedLight );
#endif`,Sp=`#if defined( USE_LOGARITHMIC_DEPTH_BUFFER )
	gl_FragDepth = vIsPerspective == 0.0 ? gl_FragCoord.z : log2( vFragDepth ) * logDepthBufFC * 0.5;
#endif`,Ep=`#if defined( USE_LOGARITHMIC_DEPTH_BUFFER )
	uniform float logDepthBufFC;
	varying float vFragDepth;
	varying float vIsPerspective;
#endif`,Tp=`#ifdef USE_LOGARITHMIC_DEPTH_BUFFER
	varying float vFragDepth;
	varying float vIsPerspective;
#endif`,Ap=`#ifdef USE_LOGARITHMIC_DEPTH_BUFFER
	vFragDepth = 1.0 + gl_Position.w;
	vIsPerspective = float( isPerspectiveMatrix( projectionMatrix ) );
#endif`,Cp=`#ifdef USE_MAP
	vec4 sampledDiffuseColor = texture2D( map, vMapUv );
	#ifdef DECODE_VIDEO_TEXTURE
		sampledDiffuseColor = sRGBTransferEOTF( sampledDiffuseColor );
	#endif
	diffuseColor *= sampledDiffuseColor;
#endif`,Rp=`#ifdef USE_MAP
	uniform sampler2D map;
#endif`,Ip=`#if defined( USE_MAP ) || defined( USE_ALPHAMAP )
	#if defined( USE_POINTS_UV )
		vec2 uv = vUv;
	#else
		vec2 uv = ( uvTransform * vec3( gl_PointCoord.x, 1.0 - gl_PointCoord.y, 1 ) ).xy;
	#endif
#endif
#ifdef USE_MAP
	diffuseColor *= texture2D( map, uv );
#endif
#ifdef USE_ALPHAMAP
	diffuseColor.a *= texture2D( alphaMap, uv ).g;
#endif`,Pp=`#if defined( USE_POINTS_UV )
	varying vec2 vUv;
#else
	#if defined( USE_MAP ) || defined( USE_ALPHAMAP )
		uniform mat3 uvTransform;
	#endif
#endif
#ifdef USE_MAP
	uniform sampler2D map;
#endif
#ifdef USE_ALPHAMAP
	uniform sampler2D alphaMap;
#endif`,Np=`float metalnessFactor = metalness;
#ifdef USE_METALNESSMAP
	vec4 texelMetalness = texture2D( metalnessMap, vMetalnessMapUv );
	metalnessFactor *= texelMetalness.b;
#endif`,Dp=`#ifdef USE_METALNESSMAP
	uniform sampler2D metalnessMap;
#endif`,Lp=`#ifdef USE_INSTANCING_MORPH
	float morphTargetInfluences[ MORPHTARGETS_COUNT ];
	float morphTargetBaseInfluence = texelFetch( morphTexture, ivec2( 0, gl_InstanceID ), 0 ).r;
	for ( int i = 0; i < MORPHTARGETS_COUNT; i ++ ) {
		morphTargetInfluences[i] =  texelFetch( morphTexture, ivec2( i + 1, gl_InstanceID ), 0 ).r;
	}
#endif`,Fp=`#if defined( USE_MORPHCOLORS )
	vColor *= morphTargetBaseInfluence;
	for ( int i = 0; i < MORPHTARGETS_COUNT; i ++ ) {
		#if defined( USE_COLOR_ALPHA )
			if ( morphTargetInfluences[ i ] != 0.0 ) vColor += getMorph( gl_VertexID, i, 2 ) * morphTargetInfluences[ i ];
		#elif defined( USE_COLOR )
			if ( morphTargetInfluences[ i ] != 0.0 ) vColor += getMorph( gl_VertexID, i, 2 ).rgb * morphTargetInfluences[ i ];
		#endif
	}
#endif`,Up=`#ifdef USE_MORPHNORMALS
	objectNormal *= morphTargetBaseInfluence;
	for ( int i = 0; i < MORPHTARGETS_COUNT; i ++ ) {
		if ( morphTargetInfluences[ i ] != 0.0 ) objectNormal += getMorph( gl_VertexID, i, 1 ).xyz * morphTargetInfluences[ i ];
	}
#endif`,Op=`#ifdef USE_MORPHTARGETS
	#ifndef USE_INSTANCING_MORPH
		uniform float morphTargetBaseInfluence;
		uniform float morphTargetInfluences[ MORPHTARGETS_COUNT ];
	#endif
	uniform sampler2DArray morphTargetsTexture;
	uniform ivec2 morphTargetsTextureSize;
	vec4 getMorph( const in int vertexIndex, const in int morphTargetIndex, const in int offset ) {
		int texelIndex = vertexIndex * MORPHTARGETS_TEXTURE_STRIDE + offset;
		int y = texelIndex / morphTargetsTextureSize.x;
		int x = texelIndex - y * morphTargetsTextureSize.x;
		ivec3 morphUV = ivec3( x, y, morphTargetIndex );
		return texelFetch( morphTargetsTexture, morphUV, 0 );
	}
#endif`,Bp=`#ifdef USE_MORPHTARGETS
	transformed *= morphTargetBaseInfluence;
	for ( int i = 0; i < MORPHTARGETS_COUNT; i ++ ) {
		if ( morphTargetInfluences[ i ] != 0.0 ) transformed += getMorph( gl_VertexID, i, 0 ).xyz * morphTargetInfluences[ i ];
	}
#endif`,zp=`float faceDirection = gl_FrontFacing ? 1.0 : - 1.0;
#ifdef FLAT_SHADED
	vec3 fdx = dFdx( vViewPosition );
	vec3 fdy = dFdy( vViewPosition );
	vec3 normal = normalize( cross( fdx, fdy ) );
#else
	vec3 normal = normalize( vNormal );
	#ifdef DOUBLE_SIDED
		normal *= faceDirection;
	#endif
#endif
#if defined( USE_NORMALMAP_TANGENTSPACE ) || defined( USE_CLEARCOAT_NORMALMAP ) || defined( USE_ANISOTROPY )
	#ifdef USE_TANGENT
		mat3 tbn = mat3( normalize( vTangent ), normalize( vBitangent ), normal );
	#else
		mat3 tbn = getTangentFrame( - vViewPosition, normal,
		#if defined( USE_NORMALMAP )
			vNormalMapUv
		#elif defined( USE_CLEARCOAT_NORMALMAP )
			vClearcoatNormalMapUv
		#else
			vUv
		#endif
		);
	#endif
	#if defined( DOUBLE_SIDED ) && ! defined( FLAT_SHADED )
		tbn[0] *= faceDirection;
		tbn[1] *= faceDirection;
	#endif
#endif
#ifdef USE_CLEARCOAT_NORMALMAP
	#ifdef USE_TANGENT
		mat3 tbn2 = mat3( normalize( vTangent ), normalize( vBitangent ), normal );
	#else
		mat3 tbn2 = getTangentFrame( - vViewPosition, normal, vClearcoatNormalMapUv );
	#endif
	#if defined( DOUBLE_SIDED ) && ! defined( FLAT_SHADED )
		tbn2[0] *= faceDirection;
		tbn2[1] *= faceDirection;
	#endif
#endif
vec3 nonPerturbedNormal = normal;`,kp=`#ifdef USE_NORMALMAP_OBJECTSPACE
	normal = texture2D( normalMap, vNormalMapUv ).xyz * 2.0 - 1.0;
	#ifdef FLIP_SIDED
		normal = - normal;
	#endif
	#ifdef DOUBLE_SIDED
		normal = normal * faceDirection;
	#endif
	normal = normalize( normalMatrix * normal );
#elif defined( USE_NORMALMAP_TANGENTSPACE )
	vec3 mapN = texture2D( normalMap, vNormalMapUv ).xyz * 2.0 - 1.0;
	mapN.xy *= normalScale;
	normal = normalize( tbn * mapN );
#elif defined( USE_BUMPMAP )
	normal = perturbNormalArb( - vViewPosition, normal, dHdxy_fwd(), faceDirection );
#endif`,Hp=`#ifndef FLAT_SHADED
	varying vec3 vNormal;
	#ifdef USE_TANGENT
		varying vec3 vTangent;
		varying vec3 vBitangent;
	#endif
#endif`,Vp=`#ifndef FLAT_SHADED
	varying vec3 vNormal;
	#ifdef USE_TANGENT
		varying vec3 vTangent;
		varying vec3 vBitangent;
	#endif
#endif`,Gp=`#ifndef FLAT_SHADED
	vNormal = normalize( transformedNormal );
	#ifdef USE_TANGENT
		vTangent = normalize( transformedTangent );
		vBitangent = normalize( cross( vNormal, vTangent ) * tangent.w );
	#endif
#endif`,Wp=`#ifdef USE_NORMALMAP
	uniform sampler2D normalMap;
	uniform vec2 normalScale;
#endif
#ifdef USE_NORMALMAP_OBJECTSPACE
	uniform mat3 normalMatrix;
#endif
#if ! defined ( USE_TANGENT ) && ( defined ( USE_NORMALMAP_TANGENTSPACE ) || defined ( USE_CLEARCOAT_NORMALMAP ) || defined( USE_ANISOTROPY ) )
	mat3 getTangentFrame( vec3 eye_pos, vec3 surf_norm, vec2 uv ) {
		vec3 q0 = dFdx( eye_pos.xyz );
		vec3 q1 = dFdy( eye_pos.xyz );
		vec2 st0 = dFdx( uv.st );
		vec2 st1 = dFdy( uv.st );
		vec3 N = surf_norm;
		vec3 q1perp = cross( q1, N );
		vec3 q0perp = cross( N, q0 );
		vec3 T = q1perp * st0.x + q0perp * st1.x;
		vec3 B = q1perp * st0.y + q0perp * st1.y;
		float det = max( dot( T, T ), dot( B, B ) );
		float scale = ( det == 0.0 ) ? 0.0 : inversesqrt( det );
		return mat3( T * scale, B * scale, N );
	}
#endif`,Xp=`#ifdef USE_CLEARCOAT
	vec3 clearcoatNormal = nonPerturbedNormal;
#endif`,$p=`#ifdef USE_CLEARCOAT_NORMALMAP
	vec3 clearcoatMapN = texture2D( clearcoatNormalMap, vClearcoatNormalMapUv ).xyz * 2.0 - 1.0;
	clearcoatMapN.xy *= clearcoatNormalScale;
	clearcoatNormal = normalize( tbn2 * clearcoatMapN );
#endif`,qp=`#ifdef USE_CLEARCOATMAP
	uniform sampler2D clearcoatMap;
#endif
#ifdef USE_CLEARCOAT_NORMALMAP
	uniform sampler2D clearcoatNormalMap;
	uniform vec2 clearcoatNormalScale;
#endif
#ifdef USE_CLEARCOAT_ROUGHNESSMAP
	uniform sampler2D clearcoatRoughnessMap;
#endif`,Yp=`#ifdef USE_IRIDESCENCEMAP
	uniform sampler2D iridescenceMap;
#endif
#ifdef USE_IRIDESCENCE_THICKNESSMAP
	uniform sampler2D iridescenceThicknessMap;
#endif`,Zp=`#ifdef OPAQUE
diffuseColor.a = 1.0;
#endif
#ifdef USE_TRANSMISSION
diffuseColor.a *= material.transmissionAlpha;
#endif
gl_FragColor = vec4( outgoingLight, diffuseColor.a );`,Jp=`vec3 packNormalToRGB( const in vec3 normal ) {
	return normalize( normal ) * 0.5 + 0.5;
}
vec3 unpackRGBToNormal( const in vec3 rgb ) {
	return 2.0 * rgb.xyz - 1.0;
}
const float PackUpscale = 256. / 255.;const float UnpackDownscale = 255. / 256.;const float ShiftRight8 = 1. / 256.;
const float Inv255 = 1. / 255.;
const vec4 PackFactors = vec4( 1.0, 256.0, 256.0 * 256.0, 256.0 * 256.0 * 256.0 );
const vec2 UnpackFactors2 = vec2( UnpackDownscale, 1.0 / PackFactors.g );
const vec3 UnpackFactors3 = vec3( UnpackDownscale / PackFactors.rg, 1.0 / PackFactors.b );
const vec4 UnpackFactors4 = vec4( UnpackDownscale / PackFactors.rgb, 1.0 / PackFactors.a );
vec4 packDepthToRGBA( const in float v ) {
	if( v <= 0.0 )
		return vec4( 0., 0., 0., 0. );
	if( v >= 1.0 )
		return vec4( 1., 1., 1., 1. );
	float vuf;
	float af = modf( v * PackFactors.a, vuf );
	float bf = modf( vuf * ShiftRight8, vuf );
	float gf = modf( vuf * ShiftRight8, vuf );
	return vec4( vuf * Inv255, gf * PackUpscale, bf * PackUpscale, af );
}
vec3 packDepthToRGB( const in float v ) {
	if( v <= 0.0 )
		return vec3( 0., 0., 0. );
	if( v >= 1.0 )
		return vec3( 1., 1., 1. );
	float vuf;
	float bf = modf( v * PackFactors.b, vuf );
	float gf = modf( vuf * ShiftRight8, vuf );
	return vec3( vuf * Inv255, gf * PackUpscale, bf );
}
vec2 packDepthToRG( const in float v ) {
	if( v <= 0.0 )
		return vec2( 0., 0. );
	if( v >= 1.0 )
		return vec2( 1., 1. );
	float vuf;
	float gf = modf( v * 256., vuf );
	return vec2( vuf * Inv255, gf );
}
float unpackRGBAToDepth( const in vec4 v ) {
	return dot( v, UnpackFactors4 );
}
float unpackRGBToDepth( const in vec3 v ) {
	return dot( v, UnpackFactors3 );
}
float unpackRGToDepth( const in vec2 v ) {
	return v.r * UnpackFactors2.r + v.g * UnpackFactors2.g;
}
vec4 pack2HalfToRGBA( const in vec2 v ) {
	vec4 r = vec4( v.x, fract( v.x * 255.0 ), v.y, fract( v.y * 255.0 ) );
	return vec4( r.x - r.y / 255.0, r.y, r.z - r.w / 255.0, r.w );
}
vec2 unpackRGBATo2Half( const in vec4 v ) {
	return vec2( v.x + ( v.y / 255.0 ), v.z + ( v.w / 255.0 ) );
}
float viewZToOrthographicDepth( const in float viewZ, const in float near, const in float far ) {
	return ( viewZ + near ) / ( near - far );
}
float orthographicDepthToViewZ( const in float depth, const in float near, const in float far ) {
	return depth * ( near - far ) - near;
}
float viewZToPerspectiveDepth( const in float viewZ, const in float near, const in float far ) {
	return ( ( near + viewZ ) * far ) / ( ( far - near ) * viewZ );
}
float perspectiveDepthToViewZ( const in float depth, const in float near, const in float far ) {
	return ( near * far ) / ( ( far - near ) * depth - far );
}`,Kp=`#ifdef PREMULTIPLIED_ALPHA
	gl_FragColor.rgb *= gl_FragColor.a;
#endif`,jp=`vec4 mvPosition = vec4( transformed, 1.0 );
#ifdef USE_BATCHING
	mvPosition = batchingMatrix * mvPosition;
#endif
#ifdef USE_INSTANCING
	mvPosition = instanceMatrix * mvPosition;
#endif
mvPosition = modelViewMatrix * mvPosition;
gl_Position = projectionMatrix * mvPosition;`,Qp=`#ifdef DITHERING
	gl_FragColor.rgb = dithering( gl_FragColor.rgb );
#endif`,em=`#ifdef DITHERING
	vec3 dithering( vec3 color ) {
		float grid_position = rand( gl_FragCoord.xy );
		vec3 dither_shift_RGB = vec3( 0.25 / 255.0, -0.25 / 255.0, 0.25 / 255.0 );
		dither_shift_RGB = mix( 2.0 * dither_shift_RGB, -2.0 * dither_shift_RGB, grid_position );
		return color + dither_shift_RGB;
	}
#endif`,tm=`float roughnessFactor = roughness;
#ifdef USE_ROUGHNESSMAP
	vec4 texelRoughness = texture2D( roughnessMap, vRoughnessMapUv );
	roughnessFactor *= texelRoughness.g;
#endif`,nm=`#ifdef USE_ROUGHNESSMAP
	uniform sampler2D roughnessMap;
#endif`,im=`#if NUM_SPOT_LIGHT_COORDS > 0
	varying vec4 vSpotLightCoord[ NUM_SPOT_LIGHT_COORDS ];
#endif
#if NUM_SPOT_LIGHT_MAPS > 0
	uniform sampler2D spotLightMap[ NUM_SPOT_LIGHT_MAPS ];
#endif
#ifdef USE_SHADOWMAP
	#if NUM_DIR_LIGHT_SHADOWS > 0
		uniform sampler2D directionalShadowMap[ NUM_DIR_LIGHT_SHADOWS ];
		varying vec4 vDirectionalShadowCoord[ NUM_DIR_LIGHT_SHADOWS ];
		struct DirectionalLightShadow {
			float shadowIntensity;
			float shadowBias;
			float shadowNormalBias;
			float shadowRadius;
			vec2 shadowMapSize;
		};
		uniform DirectionalLightShadow directionalLightShadows[ NUM_DIR_LIGHT_SHADOWS ];
	#endif
	#if NUM_SPOT_LIGHT_SHADOWS > 0
		uniform sampler2D spotShadowMap[ NUM_SPOT_LIGHT_SHADOWS ];
		struct SpotLightShadow {
			float shadowIntensity;
			float shadowBias;
			float shadowNormalBias;
			float shadowRadius;
			vec2 shadowMapSize;
		};
		uniform SpotLightShadow spotLightShadows[ NUM_SPOT_LIGHT_SHADOWS ];
	#endif
	#if NUM_POINT_LIGHT_SHADOWS > 0
		uniform sampler2D pointShadowMap[ NUM_POINT_LIGHT_SHADOWS ];
		varying vec4 vPointShadowCoord[ NUM_POINT_LIGHT_SHADOWS ];
		struct PointLightShadow {
			float shadowIntensity;
			float shadowBias;
			float shadowNormalBias;
			float shadowRadius;
			vec2 shadowMapSize;
			float shadowCameraNear;
			float shadowCameraFar;
		};
		uniform PointLightShadow pointLightShadows[ NUM_POINT_LIGHT_SHADOWS ];
	#endif
	float texture2DCompare( sampler2D depths, vec2 uv, float compare ) {
		float depth = unpackRGBAToDepth( texture2D( depths, uv ) );
		#ifdef USE_REVERSED_DEPTH_BUFFER
			return step( depth, compare );
		#else
			return step( compare, depth );
		#endif
	}
	vec2 texture2DDistribution( sampler2D shadow, vec2 uv ) {
		return unpackRGBATo2Half( texture2D( shadow, uv ) );
	}
	float VSMShadow( sampler2D shadow, vec2 uv, float compare ) {
		float occlusion = 1.0;
		vec2 distribution = texture2DDistribution( shadow, uv );
		#ifdef USE_REVERSED_DEPTH_BUFFER
			float hard_shadow = step( distribution.x, compare );
		#else
			float hard_shadow = step( compare, distribution.x );
		#endif
		if ( hard_shadow != 1.0 ) {
			float distance = compare - distribution.x;
			float variance = max( 0.00000, distribution.y * distribution.y );
			float softness_probability = variance / (variance + distance * distance );			softness_probability = clamp( ( softness_probability - 0.3 ) / ( 0.95 - 0.3 ), 0.0, 1.0 );			occlusion = clamp( max( hard_shadow, softness_probability ), 0.0, 1.0 );
		}
		return occlusion;
	}
	float getShadow( sampler2D shadowMap, vec2 shadowMapSize, float shadowIntensity, float shadowBias, float shadowRadius, vec4 shadowCoord ) {
		float shadow = 1.0;
		shadowCoord.xyz /= shadowCoord.w;
		shadowCoord.z += shadowBias;
		bool inFrustum = shadowCoord.x >= 0.0 && shadowCoord.x <= 1.0 && shadowCoord.y >= 0.0 && shadowCoord.y <= 1.0;
		bool frustumTest = inFrustum && shadowCoord.z <= 1.0;
		if ( frustumTest ) {
		#if defined( SHADOWMAP_TYPE_PCF )
			vec2 texelSize = vec2( 1.0 ) / shadowMapSize;
			float dx0 = - texelSize.x * shadowRadius;
			float dy0 = - texelSize.y * shadowRadius;
			float dx1 = + texelSize.x * shadowRadius;
			float dy1 = + texelSize.y * shadowRadius;
			float dx2 = dx0 / 2.0;
			float dy2 = dy0 / 2.0;
			float dx3 = dx1 / 2.0;
			float dy3 = dy1 / 2.0;
			shadow = (
				texture2DCompare( shadowMap, shadowCoord.xy + vec2( dx0, dy0 ), shadowCoord.z ) +
				texture2DCompare( shadowMap, shadowCoord.xy + vec2( 0.0, dy0 ), shadowCoord.z ) +
				texture2DCompare( shadowMap, shadowCoord.xy + vec2( dx1, dy0 ), shadowCoord.z ) +
				texture2DCompare( shadowMap, shadowCoord.xy + vec2( dx2, dy2 ), shadowCoord.z ) +
				texture2DCompare( shadowMap, shadowCoord.xy + vec2( 0.0, dy2 ), shadowCoord.z ) +
				texture2DCompare( shadowMap, shadowCoord.xy + vec2( dx3, dy2 ), shadowCoord.z ) +
				texture2DCompare( shadowMap, shadowCoord.xy + vec2( dx0, 0.0 ), shadowCoord.z ) +
				texture2DCompare( shadowMap, shadowCoord.xy + vec2( dx2, 0.0 ), shadowCoord.z ) +
				texture2DCompare( shadowMap, shadowCoord.xy, shadowCoord.z ) +
				texture2DCompare( shadowMap, shadowCoord.xy + vec2( dx3, 0.0 ), shadowCoord.z ) +
				texture2DCompare( shadowMap, shadowCoord.xy + vec2( dx1, 0.0 ), shadowCoord.z ) +
				texture2DCompare( shadowMap, shadowCoord.xy + vec2( dx2, dy3 ), shadowCoord.z ) +
				texture2DCompare( shadowMap, shadowCoord.xy + vec2( 0.0, dy3 ), shadowCoord.z ) +
				texture2DCompare( shadowMap, shadowCoord.xy + vec2( dx3, dy3 ), shadowCoord.z ) +
				texture2DCompare( shadowMap, shadowCoord.xy + vec2( dx0, dy1 ), shadowCoord.z ) +
				texture2DCompare( shadowMap, shadowCoord.xy + vec2( 0.0, dy1 ), shadowCoord.z ) +
				texture2DCompare( shadowMap, shadowCoord.xy + vec2( dx1, dy1 ), shadowCoord.z )
			) * ( 1.0 / 17.0 );
		#elif defined( SHADOWMAP_TYPE_PCF_SOFT )
			vec2 texelSize = vec2( 1.0 ) / shadowMapSize;
			float dx = texelSize.x;
			float dy = texelSize.y;
			vec2 uv = shadowCoord.xy;
			vec2 f = fract( uv * shadowMapSize + 0.5 );
			uv -= f * texelSize;
			shadow = (
				texture2DCompare( shadowMap, uv, shadowCoord.z ) +
				texture2DCompare( shadowMap, uv + vec2( dx, 0.0 ), shadowCoord.z ) +
				texture2DCompare( shadowMap, uv + vec2( 0.0, dy ), shadowCoord.z ) +
				texture2DCompare( shadowMap, uv + texelSize, shadowCoord.z ) +
				mix( texture2DCompare( shadowMap, uv + vec2( -dx, 0.0 ), shadowCoord.z ),
					 texture2DCompare( shadowMap, uv + vec2( 2.0 * dx, 0.0 ), shadowCoord.z ),
					 f.x ) +
				mix( texture2DCompare( shadowMap, uv + vec2( -dx, dy ), shadowCoord.z ),
					 texture2DCompare( shadowMap, uv + vec2( 2.0 * dx, dy ), shadowCoord.z ),
					 f.x ) +
				mix( texture2DCompare( shadowMap, uv + vec2( 0.0, -dy ), shadowCoord.z ),
					 texture2DCompare( shadowMap, uv + vec2( 0.0, 2.0 * dy ), shadowCoord.z ),
					 f.y ) +
				mix( texture2DCompare( shadowMap, uv + vec2( dx, -dy ), shadowCoord.z ),
					 texture2DCompare( shadowMap, uv + vec2( dx, 2.0 * dy ), shadowCoord.z ),
					 f.y ) +
				mix( mix( texture2DCompare( shadowMap, uv + vec2( -dx, -dy ), shadowCoord.z ),
						  texture2DCompare( shadowMap, uv + vec2( 2.0 * dx, -dy ), shadowCoord.z ),
						  f.x ),
					 mix( texture2DCompare( shadowMap, uv + vec2( -dx, 2.0 * dy ), shadowCoord.z ),
						  texture2DCompare( shadowMap, uv + vec2( 2.0 * dx, 2.0 * dy ), shadowCoord.z ),
						  f.x ),
					 f.y )
			) * ( 1.0 / 9.0 );
		#elif defined( SHADOWMAP_TYPE_VSM )
			shadow = VSMShadow( shadowMap, shadowCoord.xy, shadowCoord.z );
		#else
			shadow = texture2DCompare( shadowMap, shadowCoord.xy, shadowCoord.z );
		#endif
		}
		return mix( 1.0, shadow, shadowIntensity );
	}
	vec2 cubeToUV( vec3 v, float texelSizeY ) {
		vec3 absV = abs( v );
		float scaleToCube = 1.0 / max( absV.x, max( absV.y, absV.z ) );
		absV *= scaleToCube;
		v *= scaleToCube * ( 1.0 - 2.0 * texelSizeY );
		vec2 planar = v.xy;
		float almostATexel = 1.5 * texelSizeY;
		float almostOne = 1.0 - almostATexel;
		if ( absV.z >= almostOne ) {
			if ( v.z > 0.0 )
				planar.x = 4.0 - v.x;
		} else if ( absV.x >= almostOne ) {
			float signX = sign( v.x );
			planar.x = v.z * signX + 2.0 * signX;
		} else if ( absV.y >= almostOne ) {
			float signY = sign( v.y );
			planar.x = v.x + 2.0 * signY + 2.0;
			planar.y = v.z * signY - 2.0;
		}
		return vec2( 0.125, 0.25 ) * planar + vec2( 0.375, 0.75 );
	}
	float getPointShadow( sampler2D shadowMap, vec2 shadowMapSize, float shadowIntensity, float shadowBias, float shadowRadius, vec4 shadowCoord, float shadowCameraNear, float shadowCameraFar ) {
		float shadow = 1.0;
		vec3 lightToPosition = shadowCoord.xyz;
		
		float lightToPositionLength = length( lightToPosition );
		if ( lightToPositionLength - shadowCameraFar <= 0.0 && lightToPositionLength - shadowCameraNear >= 0.0 ) {
			float dp = ( lightToPositionLength - shadowCameraNear ) / ( shadowCameraFar - shadowCameraNear );			dp += shadowBias;
			vec3 bd3D = normalize( lightToPosition );
			vec2 texelSize = vec2( 1.0 ) / ( shadowMapSize * vec2( 4.0, 2.0 ) );
			#if defined( SHADOWMAP_TYPE_PCF ) || defined( SHADOWMAP_TYPE_PCF_SOFT ) || defined( SHADOWMAP_TYPE_VSM )
				vec2 offset = vec2( - 1, 1 ) * shadowRadius * texelSize.y;
				shadow = (
					texture2DCompare( shadowMap, cubeToUV( bd3D + offset.xyy, texelSize.y ), dp ) +
					texture2DCompare( shadowMap, cubeToUV( bd3D + offset.yyy, texelSize.y ), dp ) +
					texture2DCompare( shadowMap, cubeToUV( bd3D + offset.xyx, texelSize.y ), dp ) +
					texture2DCompare( shadowMap, cubeToUV( bd3D + offset.yyx, texelSize.y ), dp ) +
					texture2DCompare( shadowMap, cubeToUV( bd3D, texelSize.y ), dp ) +
					texture2DCompare( shadowMap, cubeToUV( bd3D + offset.xxy, texelSize.y ), dp ) +
					texture2DCompare( shadowMap, cubeToUV( bd3D + offset.yxy, texelSize.y ), dp ) +
					texture2DCompare( shadowMap, cubeToUV( bd3D + offset.xxx, texelSize.y ), dp ) +
					texture2DCompare( shadowMap, cubeToUV( bd3D + offset.yxx, texelSize.y ), dp )
				) * ( 1.0 / 9.0 );
			#else
				shadow = texture2DCompare( shadowMap, cubeToUV( bd3D, texelSize.y ), dp );
			#endif
		}
		return mix( 1.0, shadow, shadowIntensity );
	}
#endif`,rm=`#if NUM_SPOT_LIGHT_COORDS > 0
	uniform mat4 spotLightMatrix[ NUM_SPOT_LIGHT_COORDS ];
	varying vec4 vSpotLightCoord[ NUM_SPOT_LIGHT_COORDS ];
#endif
#ifdef USE_SHADOWMAP
	#if NUM_DIR_LIGHT_SHADOWS > 0
		uniform mat4 directionalShadowMatrix[ NUM_DIR_LIGHT_SHADOWS ];
		varying vec4 vDirectionalShadowCoord[ NUM_DIR_LIGHT_SHADOWS ];
		struct DirectionalLightShadow {
			float shadowIntensity;
			float shadowBias;
			float shadowNormalBias;
			float shadowRadius;
			vec2 shadowMapSize;
		};
		uniform DirectionalLightShadow directionalLightShadows[ NUM_DIR_LIGHT_SHADOWS ];
	#endif
	#if NUM_SPOT_LIGHT_SHADOWS > 0
		struct SpotLightShadow {
			float shadowIntensity;
			float shadowBias;
			float shadowNormalBias;
			float shadowRadius;
			vec2 shadowMapSize;
		};
		uniform SpotLightShadow spotLightShadows[ NUM_SPOT_LIGHT_SHADOWS ];
	#endif
	#if NUM_POINT_LIGHT_SHADOWS > 0
		uniform mat4 pointShadowMatrix[ NUM_POINT_LIGHT_SHADOWS ];
		varying vec4 vPointShadowCoord[ NUM_POINT_LIGHT_SHADOWS ];
		struct PointLightShadow {
			float shadowIntensity;
			float shadowBias;
			float shadowNormalBias;
			float shadowRadius;
			vec2 shadowMapSize;
			float shadowCameraNear;
			float shadowCameraFar;
		};
		uniform PointLightShadow pointLightShadows[ NUM_POINT_LIGHT_SHADOWS ];
	#endif
#endif`,sm=`#if ( defined( USE_SHADOWMAP ) && ( NUM_DIR_LIGHT_SHADOWS > 0 || NUM_POINT_LIGHT_SHADOWS > 0 ) ) || ( NUM_SPOT_LIGHT_COORDS > 0 )
	vec3 shadowWorldNormal = inverseTransformDirection( transformedNormal, viewMatrix );
	vec4 shadowWorldPosition;
#endif
#if defined( USE_SHADOWMAP )
	#if NUM_DIR_LIGHT_SHADOWS > 0
		#pragma unroll_loop_start
		for ( int i = 0; i < NUM_DIR_LIGHT_SHADOWS; i ++ ) {
			shadowWorldPosition = worldPosition + vec4( shadowWorldNormal * directionalLightShadows[ i ].shadowNormalBias, 0 );
			vDirectionalShadowCoord[ i ] = directionalShadowMatrix[ i ] * shadowWorldPosition;
		}
		#pragma unroll_loop_end
	#endif
	#if NUM_POINT_LIGHT_SHADOWS > 0
		#pragma unroll_loop_start
		for ( int i = 0; i < NUM_POINT_LIGHT_SHADOWS; i ++ ) {
			shadowWorldPosition = worldPosition + vec4( shadowWorldNormal * pointLightShadows[ i ].shadowNormalBias, 0 );
			vPointShadowCoord[ i ] = pointShadowMatrix[ i ] * shadowWorldPosition;
		}
		#pragma unroll_loop_end
	#endif
#endif
#if NUM_SPOT_LIGHT_COORDS > 0
	#pragma unroll_loop_start
	for ( int i = 0; i < NUM_SPOT_LIGHT_COORDS; i ++ ) {
		shadowWorldPosition = worldPosition;
		#if ( defined( USE_SHADOWMAP ) && UNROLLED_LOOP_INDEX < NUM_SPOT_LIGHT_SHADOWS )
			shadowWorldPosition.xyz += shadowWorldNormal * spotLightShadows[ i ].shadowNormalBias;
		#endif
		vSpotLightCoord[ i ] = spotLightMatrix[ i ] * shadowWorldPosition;
	}
	#pragma unroll_loop_end
#endif`,am=`float getShadowMask() {
	float shadow = 1.0;
	#ifdef USE_SHADOWMAP
	#if NUM_DIR_LIGHT_SHADOWS > 0
	DirectionalLightShadow directionalLight;
	#pragma unroll_loop_start
	for ( int i = 0; i < NUM_DIR_LIGHT_SHADOWS; i ++ ) {
		directionalLight = directionalLightShadows[ i ];
		shadow *= receiveShadow ? getShadow( directionalShadowMap[ i ], directionalLight.shadowMapSize, directionalLight.shadowIntensity, directionalLight.shadowBias, directionalLight.shadowRadius, vDirectionalShadowCoord[ i ] ) : 1.0;
	}
	#pragma unroll_loop_end
	#endif
	#if NUM_SPOT_LIGHT_SHADOWS > 0
	SpotLightShadow spotLight;
	#pragma unroll_loop_start
	for ( int i = 0; i < NUM_SPOT_LIGHT_SHADOWS; i ++ ) {
		spotLight = spotLightShadows[ i ];
		shadow *= receiveShadow ? getShadow( spotShadowMap[ i ], spotLight.shadowMapSize, spotLight.shadowIntensity, spotLight.shadowBias, spotLight.shadowRadius, vSpotLightCoord[ i ] ) : 1.0;
	}
	#pragma unroll_loop_end
	#endif
	#if NUM_POINT_LIGHT_SHADOWS > 0
	PointLightShadow pointLight;
	#pragma unroll_loop_start
	for ( int i = 0; i < NUM_POINT_LIGHT_SHADOWS; i ++ ) {
		pointLight = pointLightShadows[ i ];
		shadow *= receiveShadow ? getPointShadow( pointShadowMap[ i ], pointLight.shadowMapSize, pointLight.shadowIntensity, pointLight.shadowBias, pointLight.shadowRadius, vPointShadowCoord[ i ], pointLight.shadowCameraNear, pointLight.shadowCameraFar ) : 1.0;
	}
	#pragma unroll_loop_end
	#endif
	#endif
	return shadow;
}`,om=`#ifdef USE_SKINNING
	mat4 boneMatX = getBoneMatrix( skinIndex.x );
	mat4 boneMatY = getBoneMatrix( skinIndex.y );
	mat4 boneMatZ = getBoneMatrix( skinIndex.z );
	mat4 boneMatW = getBoneMatrix( skinIndex.w );
#endif`,lm=`#ifdef USE_SKINNING
	uniform mat4 bindMatrix;
	uniform mat4 bindMatrixInverse;
	uniform highp sampler2D boneTexture;
	mat4 getBoneMatrix( const in float i ) {
		int size = textureSize( boneTexture, 0 ).x;
		int j = int( i ) * 4;
		int x = j % size;
		int y = j / size;
		vec4 v1 = texelFetch( boneTexture, ivec2( x, y ), 0 );
		vec4 v2 = texelFetch( boneTexture, ivec2( x + 1, y ), 0 );
		vec4 v3 = texelFetch( boneTexture, ivec2( x + 2, y ), 0 );
		vec4 v4 = texelFetch( boneTexture, ivec2( x + 3, y ), 0 );
		return mat4( v1, v2, v3, v4 );
	}
#endif`,cm=`#ifdef USE_SKINNING
	vec4 skinVertex = bindMatrix * vec4( transformed, 1.0 );
	vec4 skinned = vec4( 0.0 );
	skinned += boneMatX * skinVertex * skinWeight.x;
	skinned += boneMatY * skinVertex * skinWeight.y;
	skinned += boneMatZ * skinVertex * skinWeight.z;
	skinned += boneMatW * skinVertex * skinWeight.w;
	transformed = ( bindMatrixInverse * skinned ).xyz;
#endif`,dm=`#ifdef USE_SKINNING
	mat4 skinMatrix = mat4( 0.0 );
	skinMatrix += skinWeight.x * boneMatX;
	skinMatrix += skinWeight.y * boneMatY;
	skinMatrix += skinWeight.z * boneMatZ;
	skinMatrix += skinWeight.w * boneMatW;
	skinMatrix = bindMatrixInverse * skinMatrix * bindMatrix;
	objectNormal = vec4( skinMatrix * vec4( objectNormal, 0.0 ) ).xyz;
	#ifdef USE_TANGENT
		objectTangent = vec4( skinMatrix * vec4( objectTangent, 0.0 ) ).xyz;
	#endif
#endif`,um=`float specularStrength;
#ifdef USE_SPECULARMAP
	vec4 texelSpecular = texture2D( specularMap, vSpecularMapUv );
	specularStrength = texelSpecular.r;
#else
	specularStrength = 1.0;
#endif`,hm=`#ifdef USE_SPECULARMAP
	uniform sampler2D specularMap;
#endif`,fm=`#if defined( TONE_MAPPING )
	gl_FragColor.rgb = toneMapping( gl_FragColor.rgb );
#endif`,pm=`#ifndef saturate
#define saturate( a ) clamp( a, 0.0, 1.0 )
#endif
uniform float toneMappingExposure;
vec3 LinearToneMapping( vec3 color ) {
	return saturate( toneMappingExposure * color );
}
vec3 ReinhardToneMapping( vec3 color ) {
	color *= toneMappingExposure;
	return saturate( color / ( vec3( 1.0 ) + color ) );
}
vec3 CineonToneMapping( vec3 color ) {
	color *= toneMappingExposure;
	color = max( vec3( 0.0 ), color - 0.004 );
	return pow( ( color * ( 6.2 * color + 0.5 ) ) / ( color * ( 6.2 * color + 1.7 ) + 0.06 ), vec3( 2.2 ) );
}
vec3 RRTAndODTFit( vec3 v ) {
	vec3 a = v * ( v + 0.0245786 ) - 0.000090537;
	vec3 b = v * ( 0.983729 * v + 0.4329510 ) + 0.238081;
	return a / b;
}
vec3 ACESFilmicToneMapping( vec3 color ) {
	const mat3 ACESInputMat = mat3(
		vec3( 0.59719, 0.07600, 0.02840 ),		vec3( 0.35458, 0.90834, 0.13383 ),
		vec3( 0.04823, 0.01566, 0.83777 )
	);
	const mat3 ACESOutputMat = mat3(
		vec3(  1.60475, -0.10208, -0.00327 ),		vec3( -0.53108,  1.10813, -0.07276 ),
		vec3( -0.07367, -0.00605,  1.07602 )
	);
	color *= toneMappingExposure / 0.6;
	color = ACESInputMat * color;
	color = RRTAndODTFit( color );
	color = ACESOutputMat * color;
	return saturate( color );
}
const mat3 LINEAR_REC2020_TO_LINEAR_SRGB = mat3(
	vec3( 1.6605, - 0.1246, - 0.0182 ),
	vec3( - 0.5876, 1.1329, - 0.1006 ),
	vec3( - 0.0728, - 0.0083, 1.1187 )
);
const mat3 LINEAR_SRGB_TO_LINEAR_REC2020 = mat3(
	vec3( 0.6274, 0.0691, 0.0164 ),
	vec3( 0.3293, 0.9195, 0.0880 ),
	vec3( 0.0433, 0.0113, 0.8956 )
);
vec3 agxDefaultContrastApprox( vec3 x ) {
	vec3 x2 = x * x;
	vec3 x4 = x2 * x2;
	return + 15.5 * x4 * x2
		- 40.14 * x4 * x
		+ 31.96 * x4
		- 6.868 * x2 * x
		+ 0.4298 * x2
		+ 0.1191 * x
		- 0.00232;
}
vec3 AgXToneMapping( vec3 color ) {
	const mat3 AgXInsetMatrix = mat3(
		vec3( 0.856627153315983, 0.137318972929847, 0.11189821299995 ),
		vec3( 0.0951212405381588, 0.761241990602591, 0.0767994186031903 ),
		vec3( 0.0482516061458583, 0.101439036467562, 0.811302368396859 )
	);
	const mat3 AgXOutsetMatrix = mat3(
		vec3( 1.1271005818144368, - 0.1413297634984383, - 0.14132976349843826 ),
		vec3( - 0.11060664309660323, 1.157823702216272, - 0.11060664309660294 ),
		vec3( - 0.016493938717834573, - 0.016493938717834257, 1.2519364065950405 )
	);
	const float AgxMinEv = - 12.47393;	const float AgxMaxEv = 4.026069;
	color *= toneMappingExposure;
	color = LINEAR_SRGB_TO_LINEAR_REC2020 * color;
	color = AgXInsetMatrix * color;
	color = max( color, 1e-10 );	color = log2( color );
	color = ( color - AgxMinEv ) / ( AgxMaxEv - AgxMinEv );
	color = clamp( color, 0.0, 1.0 );
	color = agxDefaultContrastApprox( color );
	color = AgXOutsetMatrix * color;
	color = pow( max( vec3( 0.0 ), color ), vec3( 2.2 ) );
	color = LINEAR_REC2020_TO_LINEAR_SRGB * color;
	color = clamp( color, 0.0, 1.0 );
	return color;
}
vec3 NeutralToneMapping( vec3 color ) {
	const float StartCompression = 0.8 - 0.04;
	const float Desaturation = 0.15;
	color *= toneMappingExposure;
	float x = min( color.r, min( color.g, color.b ) );
	float offset = x < 0.08 ? x - 6.25 * x * x : 0.04;
	color -= offset;
	float peak = max( color.r, max( color.g, color.b ) );
	if ( peak < StartCompression ) return color;
	float d = 1. - StartCompression;
	float newPeak = 1. - d * d / ( peak + d - StartCompression );
	color *= newPeak / peak;
	float g = 1. - 1. / ( Desaturation * ( peak - newPeak ) + 1. );
	return mix( color, vec3( newPeak ), g );
}
vec3 CustomToneMapping( vec3 color ) { return color; }`,mm=`#ifdef USE_TRANSMISSION
	material.transmission = transmission;
	material.transmissionAlpha = 1.0;
	material.thickness = thickness;
	material.attenuationDistance = attenuationDistance;
	material.attenuationColor = attenuationColor;
	#ifdef USE_TRANSMISSIONMAP
		material.transmission *= texture2D( transmissionMap, vTransmissionMapUv ).r;
	#endif
	#ifdef USE_THICKNESSMAP
		material.thickness *= texture2D( thicknessMap, vThicknessMapUv ).g;
	#endif
	vec3 pos = vWorldPosition;
	vec3 v = normalize( cameraPosition - pos );
	vec3 n = inverseTransformDirection( normal, viewMatrix );
	vec4 transmitted = getIBLVolumeRefraction(
		n, v, material.roughness, material.diffuseColor, material.specularColor, material.specularF90,
		pos, modelMatrix, viewMatrix, projectionMatrix, material.dispersion, material.ior, material.thickness,
		material.attenuationColor, material.attenuationDistance );
	material.transmissionAlpha = mix( material.transmissionAlpha, transmitted.a, material.transmission );
	totalDiffuse = mix( totalDiffuse, transmitted.rgb, material.transmission );
#endif`,gm=`#ifdef USE_TRANSMISSION
	uniform float transmission;
	uniform float thickness;
	uniform float attenuationDistance;
	uniform vec3 attenuationColor;
	#ifdef USE_TRANSMISSIONMAP
		uniform sampler2D transmissionMap;
	#endif
	#ifdef USE_THICKNESSMAP
		uniform sampler2D thicknessMap;
	#endif
	uniform vec2 transmissionSamplerSize;
	uniform sampler2D transmissionSamplerMap;
	uniform mat4 modelMatrix;
	uniform mat4 projectionMatrix;
	varying vec3 vWorldPosition;
	float w0( float a ) {
		return ( 1.0 / 6.0 ) * ( a * ( a * ( - a + 3.0 ) - 3.0 ) + 1.0 );
	}
	float w1( float a ) {
		return ( 1.0 / 6.0 ) * ( a *  a * ( 3.0 * a - 6.0 ) + 4.0 );
	}
	float w2( float a ){
		return ( 1.0 / 6.0 ) * ( a * ( a * ( - 3.0 * a + 3.0 ) + 3.0 ) + 1.0 );
	}
	float w3( float a ) {
		return ( 1.0 / 6.0 ) * ( a * a * a );
	}
	float g0( float a ) {
		return w0( a ) + w1( a );
	}
	float g1( float a ) {
		return w2( a ) + w3( a );
	}
	float h0( float a ) {
		return - 1.0 + w1( a ) / ( w0( a ) + w1( a ) );
	}
	float h1( float a ) {
		return 1.0 + w3( a ) / ( w2( a ) + w3( a ) );
	}
	vec4 bicubic( sampler2D tex, vec2 uv, vec4 texelSize, float lod ) {
		uv = uv * texelSize.zw + 0.5;
		vec2 iuv = floor( uv );
		vec2 fuv = fract( uv );
		float g0x = g0( fuv.x );
		float g1x = g1( fuv.x );
		float h0x = h0( fuv.x );
		float h1x = h1( fuv.x );
		float h0y = h0( fuv.y );
		float h1y = h1( fuv.y );
		vec2 p0 = ( vec2( iuv.x + h0x, iuv.y + h0y ) - 0.5 ) * texelSize.xy;
		vec2 p1 = ( vec2( iuv.x + h1x, iuv.y + h0y ) - 0.5 ) * texelSize.xy;
		vec2 p2 = ( vec2( iuv.x + h0x, iuv.y + h1y ) - 0.5 ) * texelSize.xy;
		vec2 p3 = ( vec2( iuv.x + h1x, iuv.y + h1y ) - 0.5 ) * texelSize.xy;
		return g0( fuv.y ) * ( g0x * textureLod( tex, p0, lod ) + g1x * textureLod( tex, p1, lod ) ) +
			g1( fuv.y ) * ( g0x * textureLod( tex, p2, lod ) + g1x * textureLod( tex, p3, lod ) );
	}
	vec4 textureBicubic( sampler2D sampler, vec2 uv, float lod ) {
		vec2 fLodSize = vec2( textureSize( sampler, int( lod ) ) );
		vec2 cLodSize = vec2( textureSize( sampler, int( lod + 1.0 ) ) );
		vec2 fLodSizeInv = 1.0 / fLodSize;
		vec2 cLodSizeInv = 1.0 / cLodSize;
		vec4 fSample = bicubic( sampler, uv, vec4( fLodSizeInv, fLodSize ), floor( lod ) );
		vec4 cSample = bicubic( sampler, uv, vec4( cLodSizeInv, cLodSize ), ceil( lod ) );
		return mix( fSample, cSample, fract( lod ) );
	}
	vec3 getVolumeTransmissionRay( const in vec3 n, const in vec3 v, const in float thickness, const in float ior, const in mat4 modelMatrix ) {
		vec3 refractionVector = refract( - v, normalize( n ), 1.0 / ior );
		vec3 modelScale;
		modelScale.x = length( vec3( modelMatrix[ 0 ].xyz ) );
		modelScale.y = length( vec3( modelMatrix[ 1 ].xyz ) );
		modelScale.z = length( vec3( modelMatrix[ 2 ].xyz ) );
		return normalize( refractionVector ) * thickness * modelScale;
	}
	float applyIorToRoughness( const in float roughness, const in float ior ) {
		return roughness * clamp( ior * 2.0 - 2.0, 0.0, 1.0 );
	}
	vec4 getTransmissionSample( const in vec2 fragCoord, const in float roughness, const in float ior ) {
		float lod = log2( transmissionSamplerSize.x ) * applyIorToRoughness( roughness, ior );
		return textureBicubic( transmissionSamplerMap, fragCoord.xy, lod );
	}
	vec3 volumeAttenuation( const in float transmissionDistance, const in vec3 attenuationColor, const in float attenuationDistance ) {
		if ( isinf( attenuationDistance ) ) {
			return vec3( 1.0 );
		} else {
			vec3 attenuationCoefficient = -log( attenuationColor ) / attenuationDistance;
			vec3 transmittance = exp( - attenuationCoefficient * transmissionDistance );			return transmittance;
		}
	}
	vec4 getIBLVolumeRefraction( const in vec3 n, const in vec3 v, const in float roughness, const in vec3 diffuseColor,
		const in vec3 specularColor, const in float specularF90, const in vec3 position, const in mat4 modelMatrix,
		const in mat4 viewMatrix, const in mat4 projMatrix, const in float dispersion, const in float ior, const in float thickness,
		const in vec3 attenuationColor, const in float attenuationDistance ) {
		vec4 transmittedLight;
		vec3 transmittance;
		#ifdef USE_DISPERSION
			float halfSpread = ( ior - 1.0 ) * 0.025 * dispersion;
			vec3 iors = vec3( ior - halfSpread, ior, ior + halfSpread );
			for ( int i = 0; i < 3; i ++ ) {
				vec3 transmissionRay = getVolumeTransmissionRay( n, v, thickness, iors[ i ], modelMatrix );
				vec3 refractedRayExit = position + transmissionRay;
				vec4 ndcPos = projMatrix * viewMatrix * vec4( refractedRayExit, 1.0 );
				vec2 refractionCoords = ndcPos.xy / ndcPos.w;
				refractionCoords += 1.0;
				refractionCoords /= 2.0;
				vec4 transmissionSample = getTransmissionSample( refractionCoords, roughness, iors[ i ] );
				transmittedLight[ i ] = transmissionSample[ i ];
				transmittedLight.a += transmissionSample.a;
				transmittance[ i ] = diffuseColor[ i ] * volumeAttenuation( length( transmissionRay ), attenuationColor, attenuationDistance )[ i ];
			}
			transmittedLight.a /= 3.0;
		#else
			vec3 transmissionRay = getVolumeTransmissionRay( n, v, thickness, ior, modelMatrix );
			vec3 refractedRayExit = position + transmissionRay;
			vec4 ndcPos = projMatrix * viewMatrix * vec4( refractedRayExit, 1.0 );
			vec2 refractionCoords = ndcPos.xy / ndcPos.w;
			refractionCoords += 1.0;
			refractionCoords /= 2.0;
			transmittedLight = getTransmissionSample( refractionCoords, roughness, ior );
			transmittance = diffuseColor * volumeAttenuation( length( transmissionRay ), attenuationColor, attenuationDistance );
		#endif
		vec3 attenuatedColor = transmittance * transmittedLight.rgb;
		vec3 F = EnvironmentBRDF( n, v, specularColor, specularF90, roughness );
		float transmittanceFactor = ( transmittance.r + transmittance.g + transmittance.b ) / 3.0;
		return vec4( ( 1.0 - F ) * attenuatedColor, 1.0 - ( 1.0 - transmittedLight.a ) * transmittanceFactor );
	}
#endif`,xm=`#if defined( USE_UV ) || defined( USE_ANISOTROPY )
	varying vec2 vUv;
#endif
#ifdef USE_MAP
	varying vec2 vMapUv;
#endif
#ifdef USE_ALPHAMAP
	varying vec2 vAlphaMapUv;
#endif
#ifdef USE_LIGHTMAP
	varying vec2 vLightMapUv;
#endif
#ifdef USE_AOMAP
	varying vec2 vAoMapUv;
#endif
#ifdef USE_BUMPMAP
	varying vec2 vBumpMapUv;
#endif
#ifdef USE_NORMALMAP
	varying vec2 vNormalMapUv;
#endif
#ifdef USE_EMISSIVEMAP
	varying vec2 vEmissiveMapUv;
#endif
#ifdef USE_METALNESSMAP
	varying vec2 vMetalnessMapUv;
#endif
#ifdef USE_ROUGHNESSMAP
	varying vec2 vRoughnessMapUv;
#endif
#ifdef USE_ANISOTROPYMAP
	varying vec2 vAnisotropyMapUv;
#endif
#ifdef USE_CLEARCOATMAP
	varying vec2 vClearcoatMapUv;
#endif
#ifdef USE_CLEARCOAT_NORMALMAP
	varying vec2 vClearcoatNormalMapUv;
#endif
#ifdef USE_CLEARCOAT_ROUGHNESSMAP
	varying vec2 vClearcoatRoughnessMapUv;
#endif
#ifdef USE_IRIDESCENCEMAP
	varying vec2 vIridescenceMapUv;
#endif
#ifdef USE_IRIDESCENCE_THICKNESSMAP
	varying vec2 vIridescenceThicknessMapUv;
#endif
#ifdef USE_SHEEN_COLORMAP
	varying vec2 vSheenColorMapUv;
#endif
#ifdef USE_SHEEN_ROUGHNESSMAP
	varying vec2 vSheenRoughnessMapUv;
#endif
#ifdef USE_SPECULARMAP
	varying vec2 vSpecularMapUv;
#endif
#ifdef USE_SPECULAR_COLORMAP
	varying vec2 vSpecularColorMapUv;
#endif
#ifdef USE_SPECULAR_INTENSITYMAP
	varying vec2 vSpecularIntensityMapUv;
#endif
#ifdef USE_TRANSMISSIONMAP
	uniform mat3 transmissionMapTransform;
	varying vec2 vTransmissionMapUv;
#endif
#ifdef USE_THICKNESSMAP
	uniform mat3 thicknessMapTransform;
	varying vec2 vThicknessMapUv;
#endif`,_m=`#if defined( USE_UV ) || defined( USE_ANISOTROPY )
	varying vec2 vUv;
#endif
#ifdef USE_MAP
	uniform mat3 mapTransform;
	varying vec2 vMapUv;
#endif
#ifdef USE_ALPHAMAP
	uniform mat3 alphaMapTransform;
	varying vec2 vAlphaMapUv;
#endif
#ifdef USE_LIGHTMAP
	uniform mat3 lightMapTransform;
	varying vec2 vLightMapUv;
#endif
#ifdef USE_AOMAP
	uniform mat3 aoMapTransform;
	varying vec2 vAoMapUv;
#endif
#ifdef USE_BUMPMAP
	uniform mat3 bumpMapTransform;
	varying vec2 vBumpMapUv;
#endif
#ifdef USE_NORMALMAP
	uniform mat3 normalMapTransform;
	varying vec2 vNormalMapUv;
#endif
#ifdef USE_DISPLACEMENTMAP
	uniform mat3 displacementMapTransform;
	varying vec2 vDisplacementMapUv;
#endif
#ifdef USE_EMISSIVEMAP
	uniform mat3 emissiveMapTransform;
	varying vec2 vEmissiveMapUv;
#endif
#ifdef USE_METALNESSMAP
	uniform mat3 metalnessMapTransform;
	varying vec2 vMetalnessMapUv;
#endif
#ifdef USE_ROUGHNESSMAP
	uniform mat3 roughnessMapTransform;
	varying vec2 vRoughnessMapUv;
#endif
#ifdef USE_ANISOTROPYMAP
	uniform mat3 anisotropyMapTransform;
	varying vec2 vAnisotropyMapUv;
#endif
#ifdef USE_CLEARCOATMAP
	uniform mat3 clearcoatMapTransform;
	varying vec2 vClearcoatMapUv;
#endif
#ifdef USE_CLEARCOAT_NORMALMAP
	uniform mat3 clearcoatNormalMapTransform;
	varying vec2 vClearcoatNormalMapUv;
#endif
#ifdef USE_CLEARCOAT_ROUGHNESSMAP
	uniform mat3 clearcoatRoughnessMapTransform;
	varying vec2 vClearcoatRoughnessMapUv;
#endif
#ifdef USE_SHEEN_COLORMAP
	uniform mat3 sheenColorMapTransform;
	varying vec2 vSheenColorMapUv;
#endif
#ifdef USE_SHEEN_ROUGHNESSMAP
	uniform mat3 sheenRoughnessMapTransform;
	varying vec2 vSheenRoughnessMapUv;
#endif
#ifdef USE_IRIDESCENCEMAP
	uniform mat3 iridescenceMapTransform;
	varying vec2 vIridescenceMapUv;
#endif
#ifdef USE_IRIDESCENCE_THICKNESSMAP
	uniform mat3 iridescenceThicknessMapTransform;
	varying vec2 vIridescenceThicknessMapUv;
#endif
#ifdef USE_SPECULARMAP
	uniform mat3 specularMapTransform;
	varying vec2 vSpecularMapUv;
#endif
#ifdef USE_SPECULAR_COLORMAP
	uniform mat3 specularColorMapTransform;
	varying vec2 vSpecularColorMapUv;
#endif
#ifdef USE_SPECULAR_INTENSITYMAP
	uniform mat3 specularIntensityMapTransform;
	varying vec2 vSpecularIntensityMapUv;
#endif
#ifdef USE_TRANSMISSIONMAP
	uniform mat3 transmissionMapTransform;
	varying vec2 vTransmissionMapUv;
#endif
#ifdef USE_THICKNESSMAP
	uniform mat3 thicknessMapTransform;
	varying vec2 vThicknessMapUv;
#endif`,ym=`#if defined( USE_UV ) || defined( USE_ANISOTROPY )
	vUv = vec3( uv, 1 ).xy;
#endif
#ifdef USE_MAP
	vMapUv = ( mapTransform * vec3( MAP_UV, 1 ) ).xy;
#endif
#ifdef USE_ALPHAMAP
	vAlphaMapUv = ( alphaMapTransform * vec3( ALPHAMAP_UV, 1 ) ).xy;
#endif
#ifdef USE_LIGHTMAP
	vLightMapUv = ( lightMapTransform * vec3( LIGHTMAP_UV, 1 ) ).xy;
#endif
#ifdef USE_AOMAP
	vAoMapUv = ( aoMapTransform * vec3( AOMAP_UV, 1 ) ).xy;
#endif
#ifdef USE_BUMPMAP
	vBumpMapUv = ( bumpMapTransform * vec3( BUMPMAP_UV, 1 ) ).xy;
#endif
#ifdef USE_NORMALMAP
	vNormalMapUv = ( normalMapTransform * vec3( NORMALMAP_UV, 1 ) ).xy;
#endif
#ifdef USE_DISPLACEMENTMAP
	vDisplacementMapUv = ( displacementMapTransform * vec3( DISPLACEMENTMAP_UV, 1 ) ).xy;
#endif
#ifdef USE_EMISSIVEMAP
	vEmissiveMapUv = ( emissiveMapTransform * vec3( EMISSIVEMAP_UV, 1 ) ).xy;
#endif
#ifdef USE_METALNESSMAP
	vMetalnessMapUv = ( metalnessMapTransform * vec3( METALNESSMAP_UV, 1 ) ).xy;
#endif
#ifdef USE_ROUGHNESSMAP
	vRoughnessMapUv = ( roughnessMapTransform * vec3( ROUGHNESSMAP_UV, 1 ) ).xy;
#endif
#ifdef USE_ANISOTROPYMAP
	vAnisotropyMapUv = ( anisotropyMapTransform * vec3( ANISOTROPYMAP_UV, 1 ) ).xy;
#endif
#ifdef USE_CLEARCOATMAP
	vClearcoatMapUv = ( clearcoatMapTransform * vec3( CLEARCOATMAP_UV, 1 ) ).xy;
#endif
#ifdef USE_CLEARCOAT_NORMALMAP
	vClearcoatNormalMapUv = ( clearcoatNormalMapTransform * vec3( CLEARCOAT_NORMALMAP_UV, 1 ) ).xy;
#endif
#ifdef USE_CLEARCOAT_ROUGHNESSMAP
	vClearcoatRoughnessMapUv = ( clearcoatRoughnessMapTransform * vec3( CLEARCOAT_ROUGHNESSMAP_UV, 1 ) ).xy;
#endif
#ifdef USE_IRIDESCENCEMAP
	vIridescenceMapUv = ( iridescenceMapTransform * vec3( IRIDESCENCEMAP_UV, 1 ) ).xy;
#endif
#ifdef USE_IRIDESCENCE_THICKNESSMAP
	vIridescenceThicknessMapUv = ( iridescenceThicknessMapTransform * vec3( IRIDESCENCE_THICKNESSMAP_UV, 1 ) ).xy;
#endif
#ifdef USE_SHEEN_COLORMAP
	vSheenColorMapUv = ( sheenColorMapTransform * vec3( SHEEN_COLORMAP_UV, 1 ) ).xy;
#endif
#ifdef USE_SHEEN_ROUGHNESSMAP
	vSheenRoughnessMapUv = ( sheenRoughnessMapTransform * vec3( SHEEN_ROUGHNESSMAP_UV, 1 ) ).xy;
#endif
#ifdef USE_SPECULARMAP
	vSpecularMapUv = ( specularMapTransform * vec3( SPECULARMAP_UV, 1 ) ).xy;
#endif
#ifdef USE_SPECULAR_COLORMAP
	vSpecularColorMapUv = ( specularColorMapTransform * vec3( SPECULAR_COLORMAP_UV, 1 ) ).xy;
#endif
#ifdef USE_SPECULAR_INTENSITYMAP
	vSpecularIntensityMapUv = ( specularIntensityMapTransform * vec3( SPECULAR_INTENSITYMAP_UV, 1 ) ).xy;
#endif
#ifdef USE_TRANSMISSIONMAP
	vTransmissionMapUv = ( transmissionMapTransform * vec3( TRANSMISSIONMAP_UV, 1 ) ).xy;
#endif
#ifdef USE_THICKNESSMAP
	vThicknessMapUv = ( thicknessMapTransform * vec3( THICKNESSMAP_UV, 1 ) ).xy;
#endif`,vm=`#if defined( USE_ENVMAP ) || defined( DISTANCE ) || defined ( USE_SHADOWMAP ) || defined ( USE_TRANSMISSION ) || NUM_SPOT_LIGHT_COORDS > 0
	vec4 worldPosition = vec4( transformed, 1.0 );
	#ifdef USE_BATCHING
		worldPosition = batchingMatrix * worldPosition;
	#endif
	#ifdef USE_INSTANCING
		worldPosition = instanceMatrix * worldPosition;
	#endif
	worldPosition = modelMatrix * worldPosition;
#endif`,bm=`varying vec2 vUv;
uniform mat3 uvTransform;
void main() {
	vUv = ( uvTransform * vec3( uv, 1 ) ).xy;
	gl_Position = vec4( position.xy, 1.0, 1.0 );
}`,wm=`uniform sampler2D t2D;
uniform float backgroundIntensity;
varying vec2 vUv;
void main() {
	vec4 texColor = texture2D( t2D, vUv );
	#ifdef DECODE_VIDEO_TEXTURE
		texColor = vec4( mix( pow( texColor.rgb * 0.9478672986 + vec3( 0.0521327014 ), vec3( 2.4 ) ), texColor.rgb * 0.0773993808, vec3( lessThanEqual( texColor.rgb, vec3( 0.04045 ) ) ) ), texColor.w );
	#endif
	texColor.rgb *= backgroundIntensity;
	gl_FragColor = texColor;
	#include <tonemapping_fragment>
	#include <colorspace_fragment>
}`,Mm=`varying vec3 vWorldDirection;
#include <common>
void main() {
	vWorldDirection = transformDirection( position, modelMatrix );
	#include <begin_vertex>
	#include <project_vertex>
	gl_Position.z = gl_Position.w;
}`,Sm=`#ifdef ENVMAP_TYPE_CUBE
	uniform samplerCube envMap;
#elif defined( ENVMAP_TYPE_CUBE_UV )
	uniform sampler2D envMap;
#endif
uniform float flipEnvMap;
uniform float backgroundBlurriness;
uniform float backgroundIntensity;
uniform mat3 backgroundRotation;
varying vec3 vWorldDirection;
#include <cube_uv_reflection_fragment>
void main() {
	#ifdef ENVMAP_TYPE_CUBE
		vec4 texColor = textureCube( envMap, backgroundRotation * vec3( flipEnvMap * vWorldDirection.x, vWorldDirection.yz ) );
	#elif defined( ENVMAP_TYPE_CUBE_UV )
		vec4 texColor = textureCubeUV( envMap, backgroundRotation * vWorldDirection, backgroundBlurriness );
	#else
		vec4 texColor = vec4( 0.0, 0.0, 0.0, 1.0 );
	#endif
	texColor.rgb *= backgroundIntensity;
	gl_FragColor = texColor;
	#include <tonemapping_fragment>
	#include <colorspace_fragment>
}`,Em=`varying vec3 vWorldDirection;
#include <common>
void main() {
	vWorldDirection = transformDirection( position, modelMatrix );
	#include <begin_vertex>
	#include <project_vertex>
	gl_Position.z = gl_Position.w;
}`,Tm=`uniform samplerCube tCube;
uniform float tFlip;
uniform float opacity;
varying vec3 vWorldDirection;
void main() {
	vec4 texColor = textureCube( tCube, vec3( tFlip * vWorldDirection.x, vWorldDirection.yz ) );
	gl_FragColor = texColor;
	gl_FragColor.a *= opacity;
	#include <tonemapping_fragment>
	#include <colorspace_fragment>
}`,Am=`#include <common>
#include <batching_pars_vertex>
#include <uv_pars_vertex>
#include <displacementmap_pars_vertex>
#include <morphtarget_pars_vertex>
#include <skinning_pars_vertex>
#include <logdepthbuf_pars_vertex>
#include <clipping_planes_pars_vertex>
varying vec2 vHighPrecisionZW;
void main() {
	#include <uv_vertex>
	#include <batching_vertex>
	#include <skinbase_vertex>
	#include <morphinstance_vertex>
	#ifdef USE_DISPLACEMENTMAP
		#include <beginnormal_vertex>
		#include <morphnormal_vertex>
		#include <skinnormal_vertex>
	#endif
	#include <begin_vertex>
	#include <morphtarget_vertex>
	#include <skinning_vertex>
	#include <displacementmap_vertex>
	#include <project_vertex>
	#include <logdepthbuf_vertex>
	#include <clipping_planes_vertex>
	vHighPrecisionZW = gl_Position.zw;
}`,Cm=`#if DEPTH_PACKING == 3200
	uniform float opacity;
#endif
#include <common>
#include <packing>
#include <uv_pars_fragment>
#include <map_pars_fragment>
#include <alphamap_pars_fragment>
#include <alphatest_pars_fragment>
#include <alphahash_pars_fragment>
#include <logdepthbuf_pars_fragment>
#include <clipping_planes_pars_fragment>
varying vec2 vHighPrecisionZW;
void main() {
	vec4 diffuseColor = vec4( 1.0 );
	#include <clipping_planes_fragment>
	#if DEPTH_PACKING == 3200
		diffuseColor.a = opacity;
	#endif
	#include <map_fragment>
	#include <alphamap_fragment>
	#include <alphatest_fragment>
	#include <alphahash_fragment>
	#include <logdepthbuf_fragment>
	#ifdef USE_REVERSED_DEPTH_BUFFER
		float fragCoordZ = vHighPrecisionZW[ 0 ] / vHighPrecisionZW[ 1 ];
	#else
		float fragCoordZ = 0.5 * vHighPrecisionZW[ 0 ] / vHighPrecisionZW[ 1 ] + 0.5;
	#endif
	#if DEPTH_PACKING == 3200
		gl_FragColor = vec4( vec3( 1.0 - fragCoordZ ), opacity );
	#elif DEPTH_PACKING == 3201
		gl_FragColor = packDepthToRGBA( fragCoordZ );
	#elif DEPTH_PACKING == 3202
		gl_FragColor = vec4( packDepthToRGB( fragCoordZ ), 1.0 );
	#elif DEPTH_PACKING == 3203
		gl_FragColor = vec4( packDepthToRG( fragCoordZ ), 0.0, 1.0 );
	#endif
}`,Rm=`#define DISTANCE
varying vec3 vWorldPosition;
#include <common>
#include <batching_pars_vertex>
#include <uv_pars_vertex>
#include <displacementmap_pars_vertex>
#include <morphtarget_pars_vertex>
#include <skinning_pars_vertex>
#include <clipping_planes_pars_vertex>
void main() {
	#include <uv_vertex>
	#include <batching_vertex>
	#include <skinbase_vertex>
	#include <morphinstance_vertex>
	#ifdef USE_DISPLACEMENTMAP
		#include <beginnormal_vertex>
		#include <morphnormal_vertex>
		#include <skinnormal_vertex>
	#endif
	#include <begin_vertex>
	#include <morphtarget_vertex>
	#include <skinning_vertex>
	#include <displacementmap_vertex>
	#include <project_vertex>
	#include <worldpos_vertex>
	#include <clipping_planes_vertex>
	vWorldPosition = worldPosition.xyz;
}`,Im=`#define DISTANCE
uniform vec3 referencePosition;
uniform float nearDistance;
uniform float farDistance;
varying vec3 vWorldPosition;
#include <common>
#include <packing>
#include <uv_pars_fragment>
#include <map_pars_fragment>
#include <alphamap_pars_fragment>
#include <alphatest_pars_fragment>
#include <alphahash_pars_fragment>
#include <clipping_planes_pars_fragment>
void main () {
	vec4 diffuseColor = vec4( 1.0 );
	#include <clipping_planes_fragment>
	#include <map_fragment>
	#include <alphamap_fragment>
	#include <alphatest_fragment>
	#include <alphahash_fragment>
	float dist = length( vWorldPosition - referencePosition );
	dist = ( dist - nearDistance ) / ( farDistance - nearDistance );
	dist = saturate( dist );
	gl_FragColor = packDepthToRGBA( dist );
}`,Pm=`varying vec3 vWorldDirection;
#include <common>
void main() {
	vWorldDirection = transformDirection( position, modelMatrix );
	#include <begin_vertex>
	#include <project_vertex>
}`,Nm=`uniform sampler2D tEquirect;
varying vec3 vWorldDirection;
#include <common>
void main() {
	vec3 direction = normalize( vWorldDirection );
	vec2 sampleUV = equirectUv( direction );
	gl_FragColor = texture2D( tEquirect, sampleUV );
	#include <tonemapping_fragment>
	#include <colorspace_fragment>
}`,Dm=`uniform float scale;
attribute float lineDistance;
varying float vLineDistance;
#include <common>
#include <uv_pars_vertex>
#include <color_pars_vertex>
#include <fog_pars_vertex>
#include <morphtarget_pars_vertex>
#include <logdepthbuf_pars_vertex>
#include <clipping_planes_pars_vertex>
void main() {
	vLineDistance = scale * lineDistance;
	#include <uv_vertex>
	#include <color_vertex>
	#include <morphinstance_vertex>
	#include <morphcolor_vertex>
	#include <begin_vertex>
	#include <morphtarget_vertex>
	#include <project_vertex>
	#include <logdepthbuf_vertex>
	#include <clipping_planes_vertex>
	#include <fog_vertex>
}`,Lm=`uniform vec3 diffuse;
uniform float opacity;
uniform float dashSize;
uniform float totalSize;
varying float vLineDistance;
#include <common>
#include <color_pars_fragment>
#include <uv_pars_fragment>
#include <map_pars_fragment>
#include <fog_pars_fragment>
#include <logdepthbuf_pars_fragment>
#include <clipping_planes_pars_fragment>
void main() {
	vec4 diffuseColor = vec4( diffuse, opacity );
	#include <clipping_planes_fragment>
	if ( mod( vLineDistance, totalSize ) > dashSize ) {
		discard;
	}
	vec3 outgoingLight = vec3( 0.0 );
	#include <logdepthbuf_fragment>
	#include <map_fragment>
	#include <color_fragment>
	outgoingLight = diffuseColor.rgb;
	#include <opaque_fragment>
	#include <tonemapping_fragment>
	#include <colorspace_fragment>
	#include <fog_fragment>
	#include <premultiplied_alpha_fragment>
}`,Fm=`#include <common>
#include <batching_pars_vertex>
#include <uv_pars_vertex>
#include <envmap_pars_vertex>
#include <color_pars_vertex>
#include <fog_pars_vertex>
#include <morphtarget_pars_vertex>
#include <skinning_pars_vertex>
#include <logdepthbuf_pars_vertex>
#include <clipping_planes_pars_vertex>
void main() {
	#include <uv_vertex>
	#include <color_vertex>
	#include <morphinstance_vertex>
	#include <morphcolor_vertex>
	#include <batching_vertex>
	#if defined ( USE_ENVMAP ) || defined ( USE_SKINNING )
		#include <beginnormal_vertex>
		#include <morphnormal_vertex>
		#include <skinbase_vertex>
		#include <skinnormal_vertex>
		#include <defaultnormal_vertex>
	#endif
	#include <begin_vertex>
	#include <morphtarget_vertex>
	#include <skinning_vertex>
	#include <project_vertex>
	#include <logdepthbuf_vertex>
	#include <clipping_planes_vertex>
	#include <worldpos_vertex>
	#include <envmap_vertex>
	#include <fog_vertex>
}`,Um=`uniform vec3 diffuse;
uniform float opacity;
#ifndef FLAT_SHADED
	varying vec3 vNormal;
#endif
#include <common>
#include <dithering_pars_fragment>
#include <color_pars_fragment>
#include <uv_pars_fragment>
#include <map_pars_fragment>
#include <alphamap_pars_fragment>
#include <alphatest_pars_fragment>
#include <alphahash_pars_fragment>
#include <aomap_pars_fragment>
#include <lightmap_pars_fragment>
#include <envmap_common_pars_fragment>
#include <envmap_pars_fragment>
#include <fog_pars_fragment>
#include <specularmap_pars_fragment>
#include <logdepthbuf_pars_fragment>
#include <clipping_planes_pars_fragment>
void main() {
	vec4 diffuseColor = vec4( diffuse, opacity );
	#include <clipping_planes_fragment>
	#include <logdepthbuf_fragment>
	#include <map_fragment>
	#include <color_fragment>
	#include <alphamap_fragment>
	#include <alphatest_fragment>
	#include <alphahash_fragment>
	#include <specularmap_fragment>
	ReflectedLight reflectedLight = ReflectedLight( vec3( 0.0 ), vec3( 0.0 ), vec3( 0.0 ), vec3( 0.0 ) );
	#ifdef USE_LIGHTMAP
		vec4 lightMapTexel = texture2D( lightMap, vLightMapUv );
		reflectedLight.indirectDiffuse += lightMapTexel.rgb * lightMapIntensity * RECIPROCAL_PI;
	#else
		reflectedLight.indirectDiffuse += vec3( 1.0 );
	#endif
	#include <aomap_fragment>
	reflectedLight.indirectDiffuse *= diffuseColor.rgb;
	vec3 outgoingLight = reflectedLight.indirectDiffuse;
	#include <envmap_fragment>
	#include <opaque_fragment>
	#include <tonemapping_fragment>
	#include <colorspace_fragment>
	#include <fog_fragment>
	#include <premultiplied_alpha_fragment>
	#include <dithering_fragment>
}`,Om=`#define LAMBERT
varying vec3 vViewPosition;
#include <common>
#include <batching_pars_vertex>
#include <uv_pars_vertex>
#include <displacementmap_pars_vertex>
#include <envmap_pars_vertex>
#include <color_pars_vertex>
#include <fog_pars_vertex>
#include <normal_pars_vertex>
#include <morphtarget_pars_vertex>
#include <skinning_pars_vertex>
#include <shadowmap_pars_vertex>
#include <logdepthbuf_pars_vertex>
#include <clipping_planes_pars_vertex>
void main() {
	#include <uv_vertex>
	#include <color_vertex>
	#include <morphinstance_vertex>
	#include <morphcolor_vertex>
	#include <batching_vertex>
	#include <beginnormal_vertex>
	#include <morphnormal_vertex>
	#include <skinbase_vertex>
	#include <skinnormal_vertex>
	#include <defaultnormal_vertex>
	#include <normal_vertex>
	#include <begin_vertex>
	#include <morphtarget_vertex>
	#include <skinning_vertex>
	#include <displacementmap_vertex>
	#include <project_vertex>
	#include <logdepthbuf_vertex>
	#include <clipping_planes_vertex>
	vViewPosition = - mvPosition.xyz;
	#include <worldpos_vertex>
	#include <envmap_vertex>
	#include <shadowmap_vertex>
	#include <fog_vertex>
}`,Bm=`#define LAMBERT
uniform vec3 diffuse;
uniform vec3 emissive;
uniform float opacity;
#include <common>
#include <packing>
#include <dithering_pars_fragment>
#include <color_pars_fragment>
#include <uv_pars_fragment>
#include <map_pars_fragment>
#include <alphamap_pars_fragment>
#include <alphatest_pars_fragment>
#include <alphahash_pars_fragment>
#include <aomap_pars_fragment>
#include <lightmap_pars_fragment>
#include <emissivemap_pars_fragment>
#include <envmap_common_pars_fragment>
#include <envmap_pars_fragment>
#include <fog_pars_fragment>
#include <bsdfs>
#include <lights_pars_begin>
#include <normal_pars_fragment>
#include <lights_lambert_pars_fragment>
#include <shadowmap_pars_fragment>
#include <bumpmap_pars_fragment>
#include <normalmap_pars_fragment>
#include <specularmap_pars_fragment>
#include <logdepthbuf_pars_fragment>
#include <clipping_planes_pars_fragment>
void main() {
	vec4 diffuseColor = vec4( diffuse, opacity );
	#include <clipping_planes_fragment>
	ReflectedLight reflectedLight = ReflectedLight( vec3( 0.0 ), vec3( 0.0 ), vec3( 0.0 ), vec3( 0.0 ) );
	vec3 totalEmissiveRadiance = emissive;
	#include <logdepthbuf_fragment>
	#include <map_fragment>
	#include <color_fragment>
	#include <alphamap_fragment>
	#include <alphatest_fragment>
	#include <alphahash_fragment>
	#include <specularmap_fragment>
	#include <normal_fragment_begin>
	#include <normal_fragment_maps>
	#include <emissivemap_fragment>
	#include <lights_lambert_fragment>
	#include <lights_fragment_begin>
	#include <lights_fragment_maps>
	#include <lights_fragment_end>
	#include <aomap_fragment>
	vec3 outgoingLight = reflectedLight.directDiffuse + reflectedLight.indirectDiffuse + totalEmissiveRadiance;
	#include <envmap_fragment>
	#include <opaque_fragment>
	#include <tonemapping_fragment>
	#include <colorspace_fragment>
	#include <fog_fragment>
	#include <premultiplied_alpha_fragment>
	#include <dithering_fragment>
}`,zm=`#define MATCAP
varying vec3 vViewPosition;
#include <common>
#include <batching_pars_vertex>
#include <uv_pars_vertex>
#include <color_pars_vertex>
#include <displacementmap_pars_vertex>
#include <fog_pars_vertex>
#include <normal_pars_vertex>
#include <morphtarget_pars_vertex>
#include <skinning_pars_vertex>
#include <logdepthbuf_pars_vertex>
#include <clipping_planes_pars_vertex>
void main() {
	#include <uv_vertex>
	#include <color_vertex>
	#include <morphinstance_vertex>
	#include <morphcolor_vertex>
	#include <batching_vertex>
	#include <beginnormal_vertex>
	#include <morphnormal_vertex>
	#include <skinbase_vertex>
	#include <skinnormal_vertex>
	#include <defaultnormal_vertex>
	#include <normal_vertex>
	#include <begin_vertex>
	#include <morphtarget_vertex>
	#include <skinning_vertex>
	#include <displacementmap_vertex>
	#include <project_vertex>
	#include <logdepthbuf_vertex>
	#include <clipping_planes_vertex>
	#include <fog_vertex>
	vViewPosition = - mvPosition.xyz;
}`,km=`#define MATCAP
uniform vec3 diffuse;
uniform float opacity;
uniform sampler2D matcap;
varying vec3 vViewPosition;
#include <common>
#include <dithering_pars_fragment>
#include <color_pars_fragment>
#include <uv_pars_fragment>
#include <map_pars_fragment>
#include <alphamap_pars_fragment>
#include <alphatest_pars_fragment>
#include <alphahash_pars_fragment>
#include <fog_pars_fragment>
#include <normal_pars_fragment>
#include <bumpmap_pars_fragment>
#include <normalmap_pars_fragment>
#include <logdepthbuf_pars_fragment>
#include <clipping_planes_pars_fragment>
void main() {
	vec4 diffuseColor = vec4( diffuse, opacity );
	#include <clipping_planes_fragment>
	#include <logdepthbuf_fragment>
	#include <map_fragment>
	#include <color_fragment>
	#include <alphamap_fragment>
	#include <alphatest_fragment>
	#include <alphahash_fragment>
	#include <normal_fragment_begin>
	#include <normal_fragment_maps>
	vec3 viewDir = normalize( vViewPosition );
	vec3 x = normalize( vec3( viewDir.z, 0.0, - viewDir.x ) );
	vec3 y = cross( viewDir, x );
	vec2 uv = vec2( dot( x, normal ), dot( y, normal ) ) * 0.495 + 0.5;
	#ifdef USE_MATCAP
		vec4 matcapColor = texture2D( matcap, uv );
	#else
		vec4 matcapColor = vec4( vec3( mix( 0.2, 0.8, uv.y ) ), 1.0 );
	#endif
	vec3 outgoingLight = diffuseColor.rgb * matcapColor.rgb;
	#include <opaque_fragment>
	#include <tonemapping_fragment>
	#include <colorspace_fragment>
	#include <fog_fragment>
	#include <premultiplied_alpha_fragment>
	#include <dithering_fragment>
}`,Hm=`#define NORMAL
#if defined( FLAT_SHADED ) || defined( USE_BUMPMAP ) || defined( USE_NORMALMAP_TANGENTSPACE )
	varying vec3 vViewPosition;
#endif
#include <common>
#include <batching_pars_vertex>
#include <uv_pars_vertex>
#include <displacementmap_pars_vertex>
#include <normal_pars_vertex>
#include <morphtarget_pars_vertex>
#include <skinning_pars_vertex>
#include <logdepthbuf_pars_vertex>
#include <clipping_planes_pars_vertex>
void main() {
	#include <uv_vertex>
	#include <batching_vertex>
	#include <beginnormal_vertex>
	#include <morphinstance_vertex>
	#include <morphnormal_vertex>
	#include <skinbase_vertex>
	#include <skinnormal_vertex>
	#include <defaultnormal_vertex>
	#include <normal_vertex>
	#include <begin_vertex>
	#include <morphtarget_vertex>
	#include <skinning_vertex>
	#include <displacementmap_vertex>
	#include <project_vertex>
	#include <logdepthbuf_vertex>
	#include <clipping_planes_vertex>
#if defined( FLAT_SHADED ) || defined( USE_BUMPMAP ) || defined( USE_NORMALMAP_TANGENTSPACE )
	vViewPosition = - mvPosition.xyz;
#endif
}`,Vm=`#define NORMAL
uniform float opacity;
#if defined( FLAT_SHADED ) || defined( USE_BUMPMAP ) || defined( USE_NORMALMAP_TANGENTSPACE )
	varying vec3 vViewPosition;
#endif
#include <packing>
#include <uv_pars_fragment>
#include <normal_pars_fragment>
#include <bumpmap_pars_fragment>
#include <normalmap_pars_fragment>
#include <logdepthbuf_pars_fragment>
#include <clipping_planes_pars_fragment>
void main() {
	vec4 diffuseColor = vec4( 0.0, 0.0, 0.0, opacity );
	#include <clipping_planes_fragment>
	#include <logdepthbuf_fragment>
	#include <normal_fragment_begin>
	#include <normal_fragment_maps>
	gl_FragColor = vec4( packNormalToRGB( normal ), diffuseColor.a );
	#ifdef OPAQUE
		gl_FragColor.a = 1.0;
	#endif
}`,Gm=`#define PHONG
varying vec3 vViewPosition;
#include <common>
#include <batching_pars_vertex>
#include <uv_pars_vertex>
#include <displacementmap_pars_vertex>
#include <envmap_pars_vertex>
#include <color_pars_vertex>
#include <fog_pars_vertex>
#include <normal_pars_vertex>
#include <morphtarget_pars_vertex>
#include <skinning_pars_vertex>
#include <shadowmap_pars_vertex>
#include <logdepthbuf_pars_vertex>
#include <clipping_planes_pars_vertex>
void main() {
	#include <uv_vertex>
	#include <color_vertex>
	#include <morphcolor_vertex>
	#include <batching_vertex>
	#include <beginnormal_vertex>
	#include <morphinstance_vertex>
	#include <morphnormal_vertex>
	#include <skinbase_vertex>
	#include <skinnormal_vertex>
	#include <defaultnormal_vertex>
	#include <normal_vertex>
	#include <begin_vertex>
	#include <morphtarget_vertex>
	#include <skinning_vertex>
	#include <displacementmap_vertex>
	#include <project_vertex>
	#include <logdepthbuf_vertex>
	#include <clipping_planes_vertex>
	vViewPosition = - mvPosition.xyz;
	#include <worldpos_vertex>
	#include <envmap_vertex>
	#include <shadowmap_vertex>
	#include <fog_vertex>
}`,Wm=`#define PHONG
uniform vec3 diffuse;
uniform vec3 emissive;
uniform vec3 specular;
uniform float shininess;
uniform float opacity;
#include <common>
#include <packing>
#include <dithering_pars_fragment>
#include <color_pars_fragment>
#include <uv_pars_fragment>
#include <map_pars_fragment>
#include <alphamap_pars_fragment>
#include <alphatest_pars_fragment>
#include <alphahash_pars_fragment>
#include <aomap_pars_fragment>
#include <lightmap_pars_fragment>
#include <emissivemap_pars_fragment>
#include <envmap_common_pars_fragment>
#include <envmap_pars_fragment>
#include <fog_pars_fragment>
#include <bsdfs>
#include <lights_pars_begin>
#include <normal_pars_fragment>
#include <lights_phong_pars_fragment>
#include <shadowmap_pars_fragment>
#include <bumpmap_pars_fragment>
#include <normalmap_pars_fragment>
#include <specularmap_pars_fragment>
#include <logdepthbuf_pars_fragment>
#include <clipping_planes_pars_fragment>
void main() {
	vec4 diffuseColor = vec4( diffuse, opacity );
	#include <clipping_planes_fragment>
	ReflectedLight reflectedLight = ReflectedLight( vec3( 0.0 ), vec3( 0.0 ), vec3( 0.0 ), vec3( 0.0 ) );
	vec3 totalEmissiveRadiance = emissive;
	#include <logdepthbuf_fragment>
	#include <map_fragment>
	#include <color_fragment>
	#include <alphamap_fragment>
	#include <alphatest_fragment>
	#include <alphahash_fragment>
	#include <specularmap_fragment>
	#include <normal_fragment_begin>
	#include <normal_fragment_maps>
	#include <emissivemap_fragment>
	#include <lights_phong_fragment>
	#include <lights_fragment_begin>
	#include <lights_fragment_maps>
	#include <lights_fragment_end>
	#include <aomap_fragment>
	vec3 outgoingLight = reflectedLight.directDiffuse + reflectedLight.indirectDiffuse + reflectedLight.directSpecular + reflectedLight.indirectSpecular + totalEmissiveRadiance;
	#include <envmap_fragment>
	#include <opaque_fragment>
	#include <tonemapping_fragment>
	#include <colorspace_fragment>
	#include <fog_fragment>
	#include <premultiplied_alpha_fragment>
	#include <dithering_fragment>
}`,Xm=`#define STANDARD
varying vec3 vViewPosition;
#ifdef USE_TRANSMISSION
	varying vec3 vWorldPosition;
#endif
#include <common>
#include <batching_pars_vertex>
#include <uv_pars_vertex>
#include <displacementmap_pars_vertex>
#include <color_pars_vertex>
#include <fog_pars_vertex>
#include <normal_pars_vertex>
#include <morphtarget_pars_vertex>
#include <skinning_pars_vertex>
#include <shadowmap_pars_vertex>
#include <logdepthbuf_pars_vertex>
#include <clipping_planes_pars_vertex>
void main() {
	#include <uv_vertex>
	#include <color_vertex>
	#include <morphinstance_vertex>
	#include <morphcolor_vertex>
	#include <batching_vertex>
	#include <beginnormal_vertex>
	#include <morphnormal_vertex>
	#include <skinbase_vertex>
	#include <skinnormal_vertex>
	#include <defaultnormal_vertex>
	#include <normal_vertex>
	#include <begin_vertex>
	#include <morphtarget_vertex>
	#include <skinning_vertex>
	#include <displacementmap_vertex>
	#include <project_vertex>
	#include <logdepthbuf_vertex>
	#include <clipping_planes_vertex>
	vViewPosition = - mvPosition.xyz;
	#include <worldpos_vertex>
	#include <shadowmap_vertex>
	#include <fog_vertex>
#ifdef USE_TRANSMISSION
	vWorldPosition = worldPosition.xyz;
#endif
}`,$m=`#define STANDARD
#ifdef PHYSICAL
	#define IOR
	#define USE_SPECULAR
#endif
uniform vec3 diffuse;
uniform vec3 emissive;
uniform float roughness;
uniform float metalness;
uniform float opacity;
#ifdef IOR
	uniform float ior;
#endif
#ifdef USE_SPECULAR
	uniform float specularIntensity;
	uniform vec3 specularColor;
	#ifdef USE_SPECULAR_COLORMAP
		uniform sampler2D specularColorMap;
	#endif
	#ifdef USE_SPECULAR_INTENSITYMAP
		uniform sampler2D specularIntensityMap;
	#endif
#endif
#ifdef USE_CLEARCOAT
	uniform float clearcoat;
	uniform float clearcoatRoughness;
#endif
#ifdef USE_DISPERSION
	uniform float dispersion;
#endif
#ifdef USE_IRIDESCENCE
	uniform float iridescence;
	uniform float iridescenceIOR;
	uniform float iridescenceThicknessMinimum;
	uniform float iridescenceThicknessMaximum;
#endif
#ifdef USE_SHEEN
	uniform vec3 sheenColor;
	uniform float sheenRoughness;
	#ifdef USE_SHEEN_COLORMAP
		uniform sampler2D sheenColorMap;
	#endif
	#ifdef USE_SHEEN_ROUGHNESSMAP
		uniform sampler2D sheenRoughnessMap;
	#endif
#endif
#ifdef USE_ANISOTROPY
	uniform vec2 anisotropyVector;
	#ifdef USE_ANISOTROPYMAP
		uniform sampler2D anisotropyMap;
	#endif
#endif
varying vec3 vViewPosition;
#include <common>
#include <packing>
#include <dithering_pars_fragment>
#include <color_pars_fragment>
#include <uv_pars_fragment>
#include <map_pars_fragment>
#include <alphamap_pars_fragment>
#include <alphatest_pars_fragment>
#include <alphahash_pars_fragment>
#include <aomap_pars_fragment>
#include <lightmap_pars_fragment>
#include <emissivemap_pars_fragment>
#include <iridescence_fragment>
#include <cube_uv_reflection_fragment>
#include <envmap_common_pars_fragment>
#include <envmap_physical_pars_fragment>
#include <fog_pars_fragment>
#include <lights_pars_begin>
#include <normal_pars_fragment>
#include <lights_physical_pars_fragment>
#include <transmission_pars_fragment>
#include <shadowmap_pars_fragment>
#include <bumpmap_pars_fragment>
#include <normalmap_pars_fragment>
#include <clearcoat_pars_fragment>
#include <iridescence_pars_fragment>
#include <roughnessmap_pars_fragment>
#include <metalnessmap_pars_fragment>
#include <logdepthbuf_pars_fragment>
#include <clipping_planes_pars_fragment>
void main() {
	vec4 diffuseColor = vec4( diffuse, opacity );
	#include <clipping_planes_fragment>
	ReflectedLight reflectedLight = ReflectedLight( vec3( 0.0 ), vec3( 0.0 ), vec3( 0.0 ), vec3( 0.0 ) );
	vec3 totalEmissiveRadiance = emissive;
	#include <logdepthbuf_fragment>
	#include <map_fragment>
	#include <color_fragment>
	#include <alphamap_fragment>
	#include <alphatest_fragment>
	#include <alphahash_fragment>
	#include <roughnessmap_fragment>
	#include <metalnessmap_fragment>
	#include <normal_fragment_begin>
	#include <normal_fragment_maps>
	#include <clearcoat_normal_fragment_begin>
	#include <clearcoat_normal_fragment_maps>
	#include <emissivemap_fragment>
	#include <lights_physical_fragment>
	#include <lights_fragment_begin>
	#include <lights_fragment_maps>
	#include <lights_fragment_end>
	#include <aomap_fragment>
	vec3 totalDiffuse = reflectedLight.directDiffuse + reflectedLight.indirectDiffuse;
	vec3 totalSpecular = reflectedLight.directSpecular + reflectedLight.indirectSpecular;
	#include <transmission_fragment>
	vec3 outgoingLight = totalDiffuse + totalSpecular + totalEmissiveRadiance;
	#ifdef USE_SHEEN
		float sheenEnergyComp = 1.0 - 0.157 * max3( material.sheenColor );
		outgoingLight = outgoingLight * sheenEnergyComp + sheenSpecularDirect + sheenSpecularIndirect;
	#endif
	#ifdef USE_CLEARCOAT
		float dotNVcc = saturate( dot( geometryClearcoatNormal, geometryViewDir ) );
		vec3 Fcc = F_Schlick( material.clearcoatF0, material.clearcoatF90, dotNVcc );
		outgoingLight = outgoingLight * ( 1.0 - material.clearcoat * Fcc ) + ( clearcoatSpecularDirect + clearcoatSpecularIndirect ) * material.clearcoat;
	#endif
	#include <opaque_fragment>
	#include <tonemapping_fragment>
	#include <colorspace_fragment>
	#include <fog_fragment>
	#include <premultiplied_alpha_fragment>
	#include <dithering_fragment>
}`,qm=`#define TOON
varying vec3 vViewPosition;
#include <common>
#include <batching_pars_vertex>
#include <uv_pars_vertex>
#include <displacementmap_pars_vertex>
#include <color_pars_vertex>
#include <fog_pars_vertex>
#include <normal_pars_vertex>
#include <morphtarget_pars_vertex>
#include <skinning_pars_vertex>
#include <shadowmap_pars_vertex>
#include <logdepthbuf_pars_vertex>
#include <clipping_planes_pars_vertex>
void main() {
	#include <uv_vertex>
	#include <color_vertex>
	#include <morphinstance_vertex>
	#include <morphcolor_vertex>
	#include <batching_vertex>
	#include <beginnormal_vertex>
	#include <morphnormal_vertex>
	#include <skinbase_vertex>
	#include <skinnormal_vertex>
	#include <defaultnormal_vertex>
	#include <normal_vertex>
	#include <begin_vertex>
	#include <morphtarget_vertex>
	#include <skinning_vertex>
	#include <displacementmap_vertex>
	#include <project_vertex>
	#include <logdepthbuf_vertex>
	#include <clipping_planes_vertex>
	vViewPosition = - mvPosition.xyz;
	#include <worldpos_vertex>
	#include <shadowmap_vertex>
	#include <fog_vertex>
}`,Ym=`#define TOON
uniform vec3 diffuse;
uniform vec3 emissive;
uniform float opacity;
#include <common>
#include <packing>
#include <dithering_pars_fragment>
#include <color_pars_fragment>
#include <uv_pars_fragment>
#include <map_pars_fragment>
#include <alphamap_pars_fragment>
#include <alphatest_pars_fragment>
#include <alphahash_pars_fragment>
#include <aomap_pars_fragment>
#include <lightmap_pars_fragment>
#include <emissivemap_pars_fragment>
#include <gradientmap_pars_fragment>
#include <fog_pars_fragment>
#include <bsdfs>
#include <lights_pars_begin>
#include <normal_pars_fragment>
#include <lights_toon_pars_fragment>
#include <shadowmap_pars_fragment>
#include <bumpmap_pars_fragment>
#include <normalmap_pars_fragment>
#include <logdepthbuf_pars_fragment>
#include <clipping_planes_pars_fragment>
void main() {
	vec4 diffuseColor = vec4( diffuse, opacity );
	#include <clipping_planes_fragment>
	ReflectedLight reflectedLight = ReflectedLight( vec3( 0.0 ), vec3( 0.0 ), vec3( 0.0 ), vec3( 0.0 ) );
	vec3 totalEmissiveRadiance = emissive;
	#include <logdepthbuf_fragment>
	#include <map_fragment>
	#include <color_fragment>
	#include <alphamap_fragment>
	#include <alphatest_fragment>
	#include <alphahash_fragment>
	#include <normal_fragment_begin>
	#include <normal_fragment_maps>
	#include <emissivemap_fragment>
	#include <lights_toon_fragment>
	#include <lights_fragment_begin>
	#include <lights_fragment_maps>
	#include <lights_fragment_end>
	#include <aomap_fragment>
	vec3 outgoingLight = reflectedLight.directDiffuse + reflectedLight.indirectDiffuse + totalEmissiveRadiance;
	#include <opaque_fragment>
	#include <tonemapping_fragment>
	#include <colorspace_fragment>
	#include <fog_fragment>
	#include <premultiplied_alpha_fragment>
	#include <dithering_fragment>
}`,Zm=`uniform float size;
uniform float scale;
#include <common>
#include <color_pars_vertex>
#include <fog_pars_vertex>
#include <morphtarget_pars_vertex>
#include <logdepthbuf_pars_vertex>
#include <clipping_planes_pars_vertex>
#ifdef USE_POINTS_UV
	varying vec2 vUv;
	uniform mat3 uvTransform;
#endif
void main() {
	#ifdef USE_POINTS_UV
		vUv = ( uvTransform * vec3( uv, 1 ) ).xy;
	#endif
	#include <color_vertex>
	#include <morphinstance_vertex>
	#include <morphcolor_vertex>
	#include <begin_vertex>
	#include <morphtarget_vertex>
	#include <project_vertex>
	gl_PointSize = size;
	#ifdef USE_SIZEATTENUATION
		bool isPerspective = isPerspectiveMatrix( projectionMatrix );
		if ( isPerspective ) gl_PointSize *= ( scale / - mvPosition.z );
	#endif
	#include <logdepthbuf_vertex>
	#include <clipping_planes_vertex>
	#include <worldpos_vertex>
	#include <fog_vertex>
}`,Jm=`uniform vec3 diffuse;
uniform float opacity;
#include <common>
#include <color_pars_fragment>
#include <map_particle_pars_fragment>
#include <alphatest_pars_fragment>
#include <alphahash_pars_fragment>
#include <fog_pars_fragment>
#include <logdepthbuf_pars_fragment>
#include <clipping_planes_pars_fragment>
void main() {
	vec4 diffuseColor = vec4( diffuse, opacity );
	#include <clipping_planes_fragment>
	vec3 outgoingLight = vec3( 0.0 );
	#include <logdepthbuf_fragment>
	#include <map_particle_fragment>
	#include <color_fragment>
	#include <alphatest_fragment>
	#include <alphahash_fragment>
	outgoingLight = diffuseColor.rgb;
	#include <opaque_fragment>
	#include <tonemapping_fragment>
	#include <colorspace_fragment>
	#include <fog_fragment>
	#include <premultiplied_alpha_fragment>
}`,Km=`#include <common>
#include <batching_pars_vertex>
#include <fog_pars_vertex>
#include <morphtarget_pars_vertex>
#include <skinning_pars_vertex>
#include <logdepthbuf_pars_vertex>
#include <shadowmap_pars_vertex>
void main() {
	#include <batching_vertex>
	#include <beginnormal_vertex>
	#include <morphinstance_vertex>
	#include <morphnormal_vertex>
	#include <skinbase_vertex>
	#include <skinnormal_vertex>
	#include <defaultnormal_vertex>
	#include <begin_vertex>
	#include <morphtarget_vertex>
	#include <skinning_vertex>
	#include <project_vertex>
	#include <logdepthbuf_vertex>
	#include <worldpos_vertex>
	#include <shadowmap_vertex>
	#include <fog_vertex>
}`,jm=`uniform vec3 color;
uniform float opacity;
#include <common>
#include <packing>
#include <fog_pars_fragment>
#include <bsdfs>
#include <lights_pars_begin>
#include <logdepthbuf_pars_fragment>
#include <shadowmap_pars_fragment>
#include <shadowmask_pars_fragment>
void main() {
	#include <logdepthbuf_fragment>
	gl_FragColor = vec4( color, opacity * ( 1.0 - getShadowMask() ) );
	#include <tonemapping_fragment>
	#include <colorspace_fragment>
	#include <fog_fragment>
}`,Qm=`uniform float rotation;
uniform vec2 center;
#include <common>
#include <uv_pars_vertex>
#include <fog_pars_vertex>
#include <logdepthbuf_pars_vertex>
#include <clipping_planes_pars_vertex>
void main() {
	#include <uv_vertex>
	vec4 mvPosition = modelViewMatrix[ 3 ];
	vec2 scale = vec2( length( modelMatrix[ 0 ].xyz ), length( modelMatrix[ 1 ].xyz ) );
	#ifndef USE_SIZEATTENUATION
		bool isPerspective = isPerspectiveMatrix( projectionMatrix );
		if ( isPerspective ) scale *= - mvPosition.z;
	#endif
	vec2 alignedPosition = ( position.xy - ( center - vec2( 0.5 ) ) ) * scale;
	vec2 rotatedPosition;
	rotatedPosition.x = cos( rotation ) * alignedPosition.x - sin( rotation ) * alignedPosition.y;
	rotatedPosition.y = sin( rotation ) * alignedPosition.x + cos( rotation ) * alignedPosition.y;
	mvPosition.xy += rotatedPosition;
	gl_Position = projectionMatrix * mvPosition;
	#include <logdepthbuf_vertex>
	#include <clipping_planes_vertex>
	#include <fog_vertex>
}`,eg=`uniform vec3 diffuse;
uniform float opacity;
#include <common>
#include <uv_pars_fragment>
#include <map_pars_fragment>
#include <alphamap_pars_fragment>
#include <alphatest_pars_fragment>
#include <alphahash_pars_fragment>
#include <fog_pars_fragment>
#include <logdepthbuf_pars_fragment>
#include <clipping_planes_pars_fragment>
void main() {
	vec4 diffuseColor = vec4( diffuse, opacity );
	#include <clipping_planes_fragment>
	vec3 outgoingLight = vec3( 0.0 );
	#include <logdepthbuf_fragment>
	#include <map_fragment>
	#include <alphamap_fragment>
	#include <alphatest_fragment>
	#include <alphahash_fragment>
	outgoingLight = diffuseColor.rgb;
	#include <opaque_fragment>
	#include <tonemapping_fragment>
	#include <colorspace_fragment>
	#include <fog_fragment>
}`,Ve={alphahash_fragment:wf,alphahash_pars_fragment:Mf,alphamap_fragment:Sf,alphamap_pars_fragment:Ef,alphatest_fragment:Tf,alphatest_pars_fragment:Af,aomap_fragment:Cf,aomap_pars_fragment:Rf,batching_pars_vertex:If,batching_vertex:Pf,begin_vertex:Nf,beginnormal_vertex:Df,bsdfs:Lf,iridescence_fragment:Ff,bumpmap_pars_fragment:Uf,clipping_planes_fragment:Of,clipping_planes_pars_fragment:Bf,clipping_planes_pars_vertex:zf,clipping_planes_vertex:kf,color_fragment:Hf,color_pars_fragment:Vf,color_pars_vertex:Gf,color_vertex:Wf,common:Xf,cube_uv_reflection_fragment:$f,defaultnormal_vertex:qf,displacementmap_pars_vertex:Yf,displacementmap_vertex:Zf,emissivemap_fragment:Jf,emissivemap_pars_fragment:Kf,colorspace_fragment:jf,colorspace_pars_fragment:Qf,envmap_fragment:ep,envmap_common_pars_fragment:tp,envmap_pars_fragment:np,envmap_pars_vertex:ip,envmap_physical_pars_fragment:pp,envmap_vertex:rp,fog_vertex:sp,fog_pars_vertex:ap,fog_fragment:op,fog_pars_fragment:lp,gradientmap_pars_fragment:cp,lightmap_pars_fragment:dp,lights_lambert_fragment:up,lights_lambert_pars_fragment:hp,lights_pars_begin:fp,lights_toon_fragment:mp,lights_toon_pars_fragment:gp,lights_phong_fragment:xp,lights_phong_pars_fragment:_p,lights_physical_fragment:yp,lights_physical_pars_fragment:vp,lights_fragment_begin:bp,lights_fragment_maps:wp,lights_fragment_end:Mp,logdepthbuf_fragment:Sp,logdepthbuf_pars_fragment:Ep,logdepthbuf_pars_vertex:Tp,logdepthbuf_vertex:Ap,map_fragment:Cp,map_pars_fragment:Rp,map_particle_fragment:Ip,map_particle_pars_fragment:Pp,metalnessmap_fragment:Np,metalnessmap_pars_fragment:Dp,morphinstance_vertex:Lp,morphcolor_vertex:Fp,morphnormal_vertex:Up,morphtarget_pars_vertex:Op,morphtarget_vertex:Bp,normal_fragment_begin:zp,normal_fragment_maps:kp,normal_pars_fragment:Hp,normal_pars_vertex:Vp,normal_vertex:Gp,normalmap_pars_fragment:Wp,clearcoat_normal_fragment_begin:Xp,clearcoat_normal_fragment_maps:$p,clearcoat_pars_fragment:qp,iridescence_pars_fragment:Yp,opaque_fragment:Zp,packing:Jp,premultiplied_alpha_fragment:Kp,project_vertex:jp,dithering_fragment:Qp,dithering_pars_fragment:em,roughnessmap_fragment:tm,roughnessmap_pars_fragment:nm,shadowmap_pars_fragment:im,shadowmap_pars_vertex:rm,shadowmap_vertex:sm,shadowmask_pars_fragment:am,skinbase_vertex:om,skinning_pars_vertex:lm,skinning_vertex:cm,skinnormal_vertex:dm,specularmap_fragment:um,specularmap_pars_fragment:hm,tonemapping_fragment:fm,tonemapping_pars_fragment:pm,transmission_fragment:mm,transmission_pars_fragment:gm,uv_pars_fragment:xm,uv_pars_vertex:_m,uv_vertex:ym,worldpos_vertex:vm,background_vert:bm,background_frag:wm,backgroundCube_vert:Mm,backgroundCube_frag:Sm,cube_vert:Em,cube_frag:Tm,depth_vert:Am,depth_frag:Cm,distanceRGBA_vert:Rm,distanceRGBA_frag:Im,equirect_vert:Pm,equirect_frag:Nm,linedashed_vert:Dm,linedashed_frag:Lm,meshbasic_vert:Fm,meshbasic_frag:Um,meshlambert_vert:Om,meshlambert_frag:Bm,meshmatcap_vert:zm,meshmatcap_frag:km,meshnormal_vert:Hm,meshnormal_frag:Vm,meshphong_vert:Gm,meshphong_frag:Wm,meshphysical_vert:Xm,meshphysical_frag:$m,meshtoon_vert:qm,meshtoon_frag:Ym,points_vert:Zm,points_frag:Jm,shadow_vert:Km,shadow_frag:jm,sprite_vert:Qm,sprite_frag:eg},oe={common:{diffuse:{value:new Ne(16777215)},opacity:{value:1},map:{value:null},mapTransform:{value:new Oe},alphaMap:{value:null},alphaMapTransform:{value:new Oe},alphaTest:{value:0}},specularmap:{specularMap:{value:null},specularMapTransform:{value:new Oe}},envmap:{envMap:{value:null},envMapRotation:{value:new Oe},flipEnvMap:{value:-1},reflectivity:{value:1},ior:{value:1.5},refractionRatio:{value:.98}},aomap:{aoMap:{value:null},aoMapIntensity:{value:1},aoMapTransform:{value:new Oe}},lightmap:{lightMap:{value:null},lightMapIntensity:{value:1},lightMapTransform:{value:new Oe}},bumpmap:{bumpMap:{value:null},bumpMapTransform:{value:new Oe},bumpScale:{value:1}},normalmap:{normalMap:{value:null},normalMapTransform:{value:new Oe},normalScale:{value:new He(1,1)}},displacementmap:{displacementMap:{value:null},displacementMapTransform:{value:new Oe},displacementScale:{value:1},displacementBias:{value:0}},emissivemap:{emissiveMap:{value:null},emissiveMapTransform:{value:new Oe}},metalnessmap:{metalnessMap:{value:null},metalnessMapTransform:{value:new Oe}},roughnessmap:{roughnessMap:{value:null},roughnessMapTransform:{value:new Oe}},gradientmap:{gradientMap:{value:null}},fog:{fogDensity:{value:25e-5},fogNear:{value:1},fogFar:{value:2e3},fogColor:{value:new Ne(16777215)}},lights:{ambientLightColor:{value:[]},lightProbe:{value:[]},directionalLights:{value:[],properties:{direction:{},color:{}}},directionalLightShadows:{value:[],properties:{shadowIntensity:1,shadowBias:{},shadowNormalBias:{},shadowRadius:{},shadowMapSize:{}}},directionalShadowMap:{value:[]},directionalShadowMatrix:{value:[]},spotLights:{value:[],properties:{color:{},position:{},direction:{},distance:{},coneCos:{},penumbraCos:{},decay:{}}},spotLightShadows:{value:[],properties:{shadowIntensity:1,shadowBias:{},shadowNormalBias:{},shadowRadius:{},shadowMapSize:{}}},spotLightMap:{value:[]},spotShadowMap:{value:[]},spotLightMatrix:{value:[]},pointLights:{value:[],properties:{color:{},position:{},decay:{},distance:{}}},pointLightShadows:{value:[],properties:{shadowIntensity:1,shadowBias:{},shadowNormalBias:{},shadowRadius:{},shadowMapSize:{},shadowCameraNear:{},shadowCameraFar:{}}},pointShadowMap:{value:[]},pointShadowMatrix:{value:[]},hemisphereLights:{value:[],properties:{direction:{},skyColor:{},groundColor:{}}},rectAreaLights:{value:[],properties:{color:{},position:{},width:{},height:{}}},ltc_1:{value:null},ltc_2:{value:null}},points:{diffuse:{value:new Ne(16777215)},opacity:{value:1},size:{value:1},scale:{value:1},map:{value:null},alphaMap:{value:null},alphaMapTransform:{value:new Oe},alphaTest:{value:0},uvTransform:{value:new Oe}},sprite:{diffuse:{value:new Ne(16777215)},opacity:{value:1},center:{value:new He(.5,.5)},rotation:{value:0},map:{value:null},mapTransform:{value:new Oe},alphaMap:{value:null},alphaMapTransform:{value:new Oe},alphaTest:{value:0}}},Nn={basic:{uniforms:Ft([oe.common,oe.specularmap,oe.envmap,oe.aomap,oe.lightmap,oe.fog]),vertexShader:Ve.meshbasic_vert,fragmentShader:Ve.meshbasic_frag},lambert:{uniforms:Ft([oe.common,oe.specularmap,oe.envmap,oe.aomap,oe.lightmap,oe.emissivemap,oe.bumpmap,oe.normalmap,oe.displacementmap,oe.fog,oe.lights,{emissive:{value:new Ne(0)}}]),vertexShader:Ve.meshlambert_vert,fragmentShader:Ve.meshlambert_frag},phong:{uniforms:Ft([oe.common,oe.specularmap,oe.envmap,oe.aomap,oe.lightmap,oe.emissivemap,oe.bumpmap,oe.normalmap,oe.displacementmap,oe.fog,oe.lights,{emissive:{value:new Ne(0)},specular:{value:new Ne(1118481)},shininess:{value:30}}]),vertexShader:Ve.meshphong_vert,fragmentShader:Ve.meshphong_frag},standard:{uniforms:Ft([oe.common,oe.envmap,oe.aomap,oe.lightmap,oe.emissivemap,oe.bumpmap,oe.normalmap,oe.displacementmap,oe.roughnessmap,oe.metalnessmap,oe.fog,oe.lights,{emissive:{value:new Ne(0)},roughness:{value:1},metalness:{value:0},envMapIntensity:{value:1}}]),vertexShader:Ve.meshphysical_vert,fragmentShader:Ve.meshphysical_frag},toon:{uniforms:Ft([oe.common,oe.aomap,oe.lightmap,oe.emissivemap,oe.bumpmap,oe.normalmap,oe.displacementmap,oe.gradientmap,oe.fog,oe.lights,{emissive:{value:new Ne(0)}}]),vertexShader:Ve.meshtoon_vert,fragmentShader:Ve.meshtoon_frag},matcap:{uniforms:Ft([oe.common,oe.bumpmap,oe.normalmap,oe.displacementmap,oe.fog,{matcap:{value:null}}]),vertexShader:Ve.meshmatcap_vert,fragmentShader:Ve.meshmatcap_frag},points:{uniforms:Ft([oe.points,oe.fog]),vertexShader:Ve.points_vert,fragmentShader:Ve.points_frag},dashed:{uniforms:Ft([oe.common,oe.fog,{scale:{value:1},dashSize:{value:1},totalSize:{value:2}}]),vertexShader:Ve.linedashed_vert,fragmentShader:Ve.linedashed_frag},depth:{uniforms:Ft([oe.common,oe.displacementmap]),vertexShader:Ve.depth_vert,fragmentShader:Ve.depth_frag},normal:{uniforms:Ft([oe.common,oe.bumpmap,oe.normalmap,oe.displacementmap,{opacity:{value:1}}]),vertexShader:Ve.meshnormal_vert,fragmentShader:Ve.meshnormal_frag},sprite:{uniforms:Ft([oe.sprite,oe.fog]),vertexShader:Ve.sprite_vert,fragmentShader:Ve.sprite_frag},background:{uniforms:{uvTransform:{value:new Oe},t2D:{value:null},backgroundIntensity:{value:1}},vertexShader:Ve.background_vert,fragmentShader:Ve.background_frag},backgroundCube:{uniforms:{envMap:{value:null},flipEnvMap:{value:-1},backgroundBlurriness:{value:0},backgroundIntensity:{value:1},backgroundRotation:{value:new Oe}},vertexShader:Ve.backgroundCube_vert,fragmentShader:Ve.backgroundCube_frag},cube:{uniforms:{tCube:{value:null},tFlip:{value:-1},opacity:{value:1}},vertexShader:Ve.cube_vert,fragmentShader:Ve.cube_frag},equirect:{uniforms:{tEquirect:{value:null}},vertexShader:Ve.equirect_vert,fragmentShader:Ve.equirect_frag},distanceRGBA:{uniforms:Ft([oe.common,oe.displacementmap,{referencePosition:{value:new N},nearDistance:{value:1},farDistance:{value:1e3}}]),vertexShader:Ve.distanceRGBA_vert,fragmentShader:Ve.distanceRGBA_frag},shadow:{uniforms:Ft([oe.lights,oe.fog,{color:{value:new Ne(0)},opacity:{value:1}}]),vertexShader:Ve.shadow_vert,fragmentShader:Ve.shadow_frag}};Nn.physical={uniforms:Ft([Nn.standard.uniforms,{clearcoat:{value:0},clearcoatMap:{value:null},clearcoatMapTransform:{value:new Oe},clearcoatNormalMap:{value:null},clearcoatNormalMapTransform:{value:new Oe},clearcoatNormalScale:{value:new He(1,1)},clearcoatRoughness:{value:0},clearcoatRoughnessMap:{value:null},clearcoatRoughnessMapTransform:{value:new Oe},dispersion:{value:0},iridescence:{value:0},iridescenceMap:{value:null},iridescenceMapTransform:{value:new Oe},iridescenceIOR:{value:1.3},iridescenceThicknessMinimum:{value:100},iridescenceThicknessMaximum:{value:400},iridescenceThicknessMap:{value:null},iridescenceThicknessMapTransform:{value:new Oe},sheen:{value:0},sheenColor:{value:new Ne(0)},sheenColorMap:{value:null},sheenColorMapTransform:{value:new Oe},sheenRoughness:{value:1},sheenRoughnessMap:{value:null},sheenRoughnessMapTransform:{value:new Oe},transmission:{value:0},transmissionMap:{value:null},transmissionMapTransform:{value:new Oe},transmissionSamplerSize:{value:new He},transmissionSamplerMap:{value:null},thickness:{value:0},thicknessMap:{value:null},thicknessMapTransform:{value:new Oe},attenuationDistance:{value:0},attenuationColor:{value:new Ne(0)},specularColor:{value:new Ne(1,1,1)},specularColorMap:{value:null},specularColorMapTransform:{value:new Oe},specularIntensity:{value:1},specularIntensityMap:{value:null},specularIntensityMapTransform:{value:new Oe},anisotropyVector:{value:new He},anisotropyMap:{value:null},anisotropyMapTransform:{value:new Oe}}]),vertexShader:Ve.meshphysical_vert,fragmentShader:Ve.meshphysical_frag};var So={r:0,b:0,g:0},Ii=new en,tg=new ct;function ng(i,e,t,n,r,s,a){let o=new Ne(0),l=s===!0?0:1,c,d,u=null,h=0,p=null;function g(M){let y=M.isScene===!0?M.background:null;return y&&y.isTexture&&(y=(M.backgroundBlurriness>0?t:e).get(y)),y}function x(M){let y=!1,C=g(M);C===null?f(o,l):C&&C.isColor&&(f(C,1),y=!0);let E=i.xr.getEnvironmentBlendMode();E==="additive"?n.buffers.color.setClear(0,0,0,1,a):E==="alpha-blend"&&n.buffers.color.setClear(0,0,0,0,a),(i.autoClear||y)&&(n.buffers.depth.setTest(!0),n.buffers.depth.setMask(!0),n.buffers.color.setMask(!0),i.clear(i.autoClearColor,i.autoClearDepth,i.autoClearStencil))}function m(M,y){let C=g(y);C&&(C.isCubeTexture||C.mapping===hs)?(d===void 0&&(d=new st(new wn(1,1,1),new tn({name:"BackgroundCubeMaterial",uniforms:Ri(Nn.backgroundCube.uniforms),vertexShader:Nn.backgroundCube.vertexShader,fragmentShader:Nn.backgroundCube.fragmentShader,side:zt,depthTest:!1,depthWrite:!1,fog:!1,allowOverride:!1})),d.geometry.deleteAttribute("normal"),d.geometry.deleteAttribute("uv"),d.onBeforeRender=function(E,R,P){this.matrixWorld.copyPosition(P.matrixWorld)},Object.defineProperty(d.material,"envMap",{get:function(){return this.uniforms.envMap.value}}),r.update(d)),Ii.copy(y.backgroundRotation),Ii.x*=-1,Ii.y*=-1,Ii.z*=-1,C.isCubeTexture&&C.isRenderTargetTexture===!1&&(Ii.y*=-1,Ii.z*=-1),d.material.uniforms.envMap.value=C,d.material.uniforms.flipEnvMap.value=C.isCubeTexture&&C.isRenderTargetTexture===!1?-1:1,d.material.uniforms.backgroundBlurriness.value=y.backgroundBlurriness,d.material.uniforms.backgroundIntensity.value=y.backgroundIntensity,d.material.uniforms.backgroundRotation.value.setFromMatrix4(tg.makeRotationFromEuler(Ii)),d.material.toneMapped=$e.getTransfer(C.colorSpace)!==Ke,(u!==C||h!==C.version||p!==i.toneMapping)&&(d.material.needsUpdate=!0,u=C,h=C.version,p=i.toneMapping),d.layers.enableAll(),M.unshift(d,d.geometry,d.material,0,0,null)):C&&C.isTexture&&(c===void 0&&(c=new st(new Ei(2,2),new tn({name:"BackgroundMaterial",uniforms:Ri(Nn.background.uniforms),vertexShader:Nn.background.vertexShader,fragmentShader:Nn.background.fragmentShader,side:Vn,depthTest:!1,depthWrite:!1,fog:!1,allowOverride:!1})),c.geometry.deleteAttribute("normal"),Object.defineProperty(c.material,"map",{get:function(){return this.uniforms.t2D.value}}),r.update(c)),c.material.uniforms.t2D.value=C,c.material.uniforms.backgroundIntensity.value=y.backgroundIntensity,c.material.toneMapped=$e.getTransfer(C.colorSpace)!==Ke,C.matrixAutoUpdate===!0&&C.updateMatrix(),c.material.uniforms.uvTransform.value.copy(C.matrix),(u!==C||h!==C.version||p!==i.toneMapping)&&(c.material.needsUpdate=!0,u=C,h=C.version,p=i.toneMapping),c.layers.enableAll(),M.unshift(c,c.geometry,c.material,0,0,null))}function f(M,y){M.getRGB(So,ql(i)),n.buffers.color.setClear(So.r,So.g,So.b,y,a)}function S(){d!==void 0&&(d.geometry.dispose(),d.material.dispose(),d=void 0),c!==void 0&&(c.geometry.dispose(),c.material.dispose(),c=void 0)}return{getClearColor:function(){return o},setClearColor:function(M,y=1){o.set(M),l=y,f(o,l)},getClearAlpha:function(){return l},setClearAlpha:function(M){l=M,f(o,l)},render:x,addToRenderList:m,dispose:S}}function ig(i,e){let t=i.getParameter(i.MAX_VERTEX_ATTRIBS),n={},r=h(null),s=r,a=!1;function o(v,T,D,F,B){let k=!1,W=u(F,D,T);s!==W&&(s=W,c(s.object)),k=p(v,F,D,B),k&&g(v,F,D,B),B!==null&&e.update(B,i.ELEMENT_ARRAY_BUFFER),(k||a)&&(a=!1,y(v,T,D,F),B!==null&&i.bindBuffer(i.ELEMENT_ARRAY_BUFFER,e.get(B).buffer))}function l(){return i.createVertexArray()}function c(v){return i.bindVertexArray(v)}function d(v){return i.deleteVertexArray(v)}function u(v,T,D){let F=D.wireframe===!0,B=n[v.id];B===void 0&&(B={},n[v.id]=B);let k=B[T.id];k===void 0&&(k={},B[T.id]=k);let W=k[F];return W===void 0&&(W=h(l()),k[F]=W),W}function h(v){let T=[],D=[],F=[];for(let B=0;B<t;B++)T[B]=0,D[B]=0,F[B]=0;return{geometry:null,program:null,wireframe:!1,newAttributes:T,enabledAttributes:D,attributeDivisors:F,object:v,attributes:{},index:null}}function p(v,T,D,F){let B=s.attributes,k=T.attributes,W=0,X=D.getAttributes();for(let H in X)if(X[H].location>=0){let ne=B[H],fe=k[H];if(fe===void 0&&(H==="instanceMatrix"&&v.instanceMatrix&&(fe=v.instanceMatrix),H==="instanceColor"&&v.instanceColor&&(fe=v.instanceColor)),ne===void 0||ne.attribute!==fe||fe&&ne.data!==fe.data)return!0;W++}return s.attributesNum!==W||s.index!==F}function g(v,T,D,F){let B={},k=T.attributes,W=0,X=D.getAttributes();for(let H in X)if(X[H].location>=0){let ne=k[H];ne===void 0&&(H==="instanceMatrix"&&v.instanceMatrix&&(ne=v.instanceMatrix),H==="instanceColor"&&v.instanceColor&&(ne=v.instanceColor));let fe={};fe.attribute=ne,ne&&ne.data&&(fe.data=ne.data),B[H]=fe,W++}s.attributes=B,s.attributesNum=W,s.index=F}function x(){let v=s.newAttributes;for(let T=0,D=v.length;T<D;T++)v[T]=0}function m(v){f(v,0)}function f(v,T){let D=s.newAttributes,F=s.enabledAttributes,B=s.attributeDivisors;D[v]=1,F[v]===0&&(i.enableVertexAttribArray(v),F[v]=1),B[v]!==T&&(i.vertexAttribDivisor(v,T),B[v]=T)}function S(){let v=s.newAttributes,T=s.enabledAttributes;for(let D=0,F=T.length;D<F;D++)T[D]!==v[D]&&(i.disableVertexAttribArray(D),T[D]=0)}function M(v,T,D,F,B,k,W){W===!0?i.vertexAttribIPointer(v,T,D,B,k):i.vertexAttribPointer(v,T,D,F,B,k)}function y(v,T,D,F){x();let B=F.attributes,k=D.getAttributes(),W=T.defaultAttributeValues;for(let X in k){let H=k[X];if(H.location>=0){let Q=B[X];if(Q===void 0&&(X==="instanceMatrix"&&v.instanceMatrix&&(Q=v.instanceMatrix),X==="instanceColor"&&v.instanceColor&&(Q=v.instanceColor)),Q!==void 0){let ne=Q.normalized,fe=Q.itemSize,De=e.get(Q);if(De===void 0)continue;let Xe=De.buffer,Ze=De.type,Fe=De.bytesPerElement,Y=Ze===i.INT||Ze===i.UNSIGNED_INT||Q.gpuType===Ga;if(Q.isInterleavedBufferAttribute){let J=Q.data,pe=J.stride,Ce=Q.offset;if(J.isInstancedInterleavedBuffer){for(let ge=0;ge<H.locationSize;ge++)f(H.location+ge,J.meshPerAttribute);v.isInstancedMesh!==!0&&F._maxInstanceCount===void 0&&(F._maxInstanceCount=J.meshPerAttribute*J.count)}else for(let ge=0;ge<H.locationSize;ge++)m(H.location+ge);i.bindBuffer(i.ARRAY_BUFFER,Xe);for(let ge=0;ge<H.locationSize;ge++)M(H.location+ge,fe/H.locationSize,Ze,ne,pe*Fe,(Ce+fe/H.locationSize*ge)*Fe,Y)}else{if(Q.isInstancedBufferAttribute){for(let J=0;J<H.locationSize;J++)f(H.location+J,Q.meshPerAttribute);v.isInstancedMesh!==!0&&F._maxInstanceCount===void 0&&(F._maxInstanceCount=Q.meshPerAttribute*Q.count)}else for(let J=0;J<H.locationSize;J++)m(H.location+J);i.bindBuffer(i.ARRAY_BUFFER,Xe);for(let J=0;J<H.locationSize;J++)M(H.location+J,fe/H.locationSize,Ze,ne,fe*Fe,fe/H.locationSize*J*Fe,Y)}}else if(W!==void 0){let ne=W[X];if(ne!==void 0)switch(ne.length){case 2:i.vertexAttrib2fv(H.location,ne);break;case 3:i.vertexAttrib3fv(H.location,ne);break;case 4:i.vertexAttrib4fv(H.location,ne);break;default:i.vertexAttrib1fv(H.location,ne)}}}}S()}function C(){P();for(let v in n){let T=n[v];for(let D in T){let F=T[D];for(let B in F)d(F[B].object),delete F[B];delete T[D]}delete n[v]}}function E(v){if(n[v.id]===void 0)return;let T=n[v.id];for(let D in T){let F=T[D];for(let B in F)d(F[B].object),delete F[B];delete T[D]}delete n[v.id]}function R(v){for(let T in n){let D=n[T];if(D[v.id]===void 0)continue;let F=D[v.id];for(let B in F)d(F[B].object),delete F[B];delete D[v.id]}}function P(){w(),a=!0,s!==r&&(s=r,c(s.object))}function w(){r.geometry=null,r.program=null,r.wireframe=!1}return{setup:o,reset:P,resetDefaultState:w,dispose:C,releaseStatesOfGeometry:E,releaseStatesOfProgram:R,initAttributes:x,enableAttribute:m,disableUnusedAttributes:S}}function rg(i,e,t){let n;function r(c){n=c}function s(c,d){i.drawArrays(n,c,d),t.update(d,n,1)}function a(c,d,u){u!==0&&(i.drawArraysInstanced(n,c,d,u),t.update(d,n,u))}function o(c,d,u){if(u===0)return;e.get("WEBGL_multi_draw").multiDrawArraysWEBGL(n,c,0,d,0,u);let p=0;for(let g=0;g<u;g++)p+=d[g];t.update(p,n,1)}function l(c,d,u,h){if(u===0)return;let p=e.get("WEBGL_multi_draw");if(p===null)for(let g=0;g<c.length;g++)a(c[g],d[g],h[g]);else{p.multiDrawArraysInstancedWEBGL(n,c,0,d,0,h,0,u);let g=0;for(let x=0;x<u;x++)g+=d[x]*h[x];t.update(g,n,1)}}this.setMode=r,this.render=s,this.renderInstances=a,this.renderMultiDraw=o,this.renderMultiDrawInstances=l}function sg(i,e,t,n){let r;function s(){if(r!==void 0)return r;if(e.has("EXT_texture_filter_anisotropic")===!0){let R=e.get("EXT_texture_filter_anisotropic");r=i.getParameter(R.MAX_TEXTURE_MAX_ANISOTROPY_EXT)}else r=0;return r}function a(R){return!(R!==un&&n.convert(R)!==i.getParameter(i.IMPLEMENTATION_COLOR_READ_FORMAT))}function o(R){let P=R===xr&&(e.has("EXT_color_buffer_half_float")||e.has("EXT_color_buffer_float"));return!(R!==Mn&&n.convert(R)!==i.getParameter(i.IMPLEMENTATION_COLOR_READ_TYPE)&&R!==Pn&&!P)}function l(R){if(R==="highp"){if(i.getShaderPrecisionFormat(i.VERTEX_SHADER,i.HIGH_FLOAT).precision>0&&i.getShaderPrecisionFormat(i.FRAGMENT_SHADER,i.HIGH_FLOAT).precision>0)return"highp";R="mediump"}return R==="mediump"&&i.getShaderPrecisionFormat(i.VERTEX_SHADER,i.MEDIUM_FLOAT).precision>0&&i.getShaderPrecisionFormat(i.FRAGMENT_SHADER,i.MEDIUM_FLOAT).precision>0?"mediump":"lowp"}let c=t.precision!==void 0?t.precision:"highp",d=l(c);d!==c&&(console.warn("THREE.WebGLRenderer:",c,"not supported, using",d,"instead."),c=d);let u=t.logarithmicDepthBuffer===!0,h=t.reversedDepthBuffer===!0&&e.has("EXT_clip_control"),p=i.getParameter(i.MAX_TEXTURE_IMAGE_UNITS),g=i.getParameter(i.MAX_VERTEX_TEXTURE_IMAGE_UNITS),x=i.getParameter(i.MAX_TEXTURE_SIZE),m=i.getParameter(i.MAX_CUBE_MAP_TEXTURE_SIZE),f=i.getParameter(i.MAX_VERTEX_ATTRIBS),S=i.getParameter(i.MAX_VERTEX_UNIFORM_VECTORS),M=i.getParameter(i.MAX_VARYING_VECTORS),y=i.getParameter(i.MAX_FRAGMENT_UNIFORM_VECTORS),C=g>0,E=i.getParameter(i.MAX_SAMPLES);return{isWebGL2:!0,getMaxAnisotropy:s,getMaxPrecision:l,textureFormatReadable:a,textureTypeReadable:o,precision:c,logarithmicDepthBuffer:u,reversedDepthBuffer:h,maxTextures:p,maxVertexTextures:g,maxTextureSize:x,maxCubemapSize:m,maxAttributes:f,maxVertexUniforms:S,maxVaryings:M,maxFragmentUniforms:y,vertexTextures:C,maxSamples:E}}function ag(i){let e=this,t=null,n=0,r=!1,s=!1,a=new Tn,o=new Oe,l={value:null,needsUpdate:!1};this.uniform=l,this.numPlanes=0,this.numIntersection=0,this.init=function(u,h){let p=u.length!==0||h||n!==0||r;return r=h,n=u.length,p},this.beginShadows=function(){s=!0,d(null)},this.endShadows=function(){s=!1},this.setGlobalState=function(u,h){t=d(u,h,0)},this.setState=function(u,h,p){let g=u.clippingPlanes,x=u.clipIntersection,m=u.clipShadows,f=i.get(u);if(!r||g===null||g.length===0||s&&!m)s?d(null):c();else{let S=s?0:n,M=S*4,y=f.clippingState||null;l.value=y,y=d(g,h,M,p);for(let C=0;C!==M;++C)y[C]=t[C];f.clippingState=y,this.numIntersection=x?this.numPlanes:0,this.numPlanes+=S}};function c(){l.value!==t&&(l.value=t,l.needsUpdate=n>0),e.numPlanes=n,e.numIntersection=0}function d(u,h,p,g){let x=u!==null?u.length:0,m=null;if(x!==0){if(m=l.value,g!==!0||m===null){let f=p+x*4,S=h.matrixWorldInverse;o.getNormalMatrix(S),(m===null||m.length<f)&&(m=new Float32Array(f));for(let M=0,y=p;M!==x;++M,y+=4)a.copy(u[M]).applyMatrix4(S,o),a.normal.toArray(m,y),m[y+3]=a.constant}l.value=m,l.needsUpdate=!0}return e.numPlanes=x,e.numIntersection=0,m}}function og(i){let e=new WeakMap;function t(a,o){return o===ka?a.mapping=Ai:o===Ha&&(a.mapping=Ci),a}function n(a){if(a&&a.isTexture){let o=a.mapping;if(o===ka||o===Ha)if(e.has(a)){let l=e.get(a).texture;return t(l,a.mapping)}else{let l=a.image;if(l&&l.height>0){let c=new ga(l.height);return c.fromEquirectangularTexture(i,a),e.set(a,c),a.addEventListener("dispose",r),t(c.texture,a.mapping)}else return null}}return a}function r(a){let o=a.target;o.removeEventListener("dispose",r);let l=e.get(o);l!==void 0&&(e.delete(o),l.dispose())}function s(){e=new WeakMap}return{get:n,dispose:s}}var br=4,au=[.125,.215,.35,.446,.526,.582],Di=20,Kl=new os,ou=new Ne,jl=null,Ql=0,ec=0,tc=!1,Ni=(1+Math.sqrt(5))/2,vr=1/Ni,lu=[new N(-Ni,vr,0),new N(Ni,vr,0),new N(-vr,0,Ni),new N(vr,0,Ni),new N(0,Ni,-vr),new N(0,Ni,vr),new N(-1,1,-1),new N(1,1,-1),new N(-1,1,1),new N(1,1,1)],lg=new N,Ao=class{constructor(e){this._renderer=e,this._pingPongRenderTarget=null,this._lodMax=0,this._cubeSize=0,this._lodPlanes=[],this._sizeLods=[],this._sigmas=[],this._blurMaterial=null,this._cubemapMaterial=null,this._equirectMaterial=null,this._compileMaterial(this._blurMaterial)}fromScene(e,t=0,n=.1,r=100,s={}){let{size:a=256,position:o=lg}=s;jl=this._renderer.getRenderTarget(),Ql=this._renderer.getActiveCubeFace(),ec=this._renderer.getActiveMipmapLevel(),tc=this._renderer.xr.enabled,this._renderer.xr.enabled=!1,this._setSize(a);let l=this._allocateTargets();return l.depthBuffer=!0,this._sceneToCubeUV(e,n,r,l,o),t>0&&this._blur(l,0,0,t),this._applyPMREM(l),this._cleanup(l),l}fromEquirectangular(e,t=null){return this._fromTexture(e,t)}fromCubemap(e,t=null){return this._fromTexture(e,t)}compileCubemapShader(){this._cubemapMaterial===null&&(this._cubemapMaterial=uu(),this._compileMaterial(this._cubemapMaterial))}compileEquirectangularShader(){this._equirectMaterial===null&&(this._equirectMaterial=du(),this._compileMaterial(this._equirectMaterial))}dispose(){this._dispose(),this._cubemapMaterial!==null&&this._cubemapMaterial.dispose(),this._equirectMaterial!==null&&this._equirectMaterial.dispose()}_setSize(e){this._lodMax=Math.floor(Math.log2(e)),this._cubeSize=Math.pow(2,this._lodMax)}_dispose(){this._blurMaterial!==null&&this._blurMaterial.dispose(),this._pingPongRenderTarget!==null&&this._pingPongRenderTarget.dispose();for(let e=0;e<this._lodPlanes.length;e++)this._lodPlanes[e].dispose()}_cleanup(e){this._renderer.setRenderTarget(jl,Ql,ec),this._renderer.xr.enabled=tc,e.scissorTest=!1,Eo(e,0,0,e.width,e.height)}_fromTexture(e,t){e.mapping===Ai||e.mapping===Ci?this._setSize(e.image.length===0?16:e.image[0].width||e.image[0].image.width):this._setSize(e.image.width/4),jl=this._renderer.getRenderTarget(),Ql=this._renderer.getActiveCubeFace(),ec=this._renderer.getActiveMipmapLevel(),tc=this._renderer.xr.enabled,this._renderer.xr.enabled=!1;let n=t||this._allocateTargets();return this._textureToCubeUV(e,n),this._applyPMREM(n),this._cleanup(n),n}_allocateTargets(){let e=3*Math.max(this._cubeSize,112),t=4*this._cubeSize,n={magFilter:vn,minFilter:vn,generateMipmaps:!1,type:xr,format:un,colorSpace:Si,depthBuffer:!1},r=cu(e,t,n);if(this._pingPongRenderTarget===null||this._pingPongRenderTarget.width!==e||this._pingPongRenderTarget.height!==t){this._pingPongRenderTarget!==null&&this._dispose(),this._pingPongRenderTarget=cu(e,t,n);let{_lodMax:s}=this;({sizeLods:this._sizeLods,lodPlanes:this._lodPlanes,sigmas:this._sigmas}=cg(s)),this._blurMaterial=dg(s,e,t)}return r}_compileMaterial(e){let t=new st(this._lodPlanes[0],e);this._renderer.compile(t,Kl)}_sceneToCubeUV(e,t,n,r,s){let l=new Dt(90,1,t,n),c=[1,-1,1,1,1,1],d=[1,1,1,-1,-1,-1],u=this._renderer,h=u.autoClear,p=u.toneMapping;u.getClearColor(ou),u.toneMapping=$n,u.autoClear=!1,u.state.buffers.depth.getReversed()&&(u.setRenderTarget(r),u.clearDepth(),u.setRenderTarget(null));let x=new Xt({name:"PMREM.Background",side:zt,depthWrite:!1,depthTest:!1}),m=new st(new wn,x),f=!1,S=e.background;S?S.isColor&&(x.color.copy(S),e.background=null,f=!0):(x.color.copy(ou),f=!0);for(let M=0;M<6;M++){let y=M%3;y===0?(l.up.set(0,c[M],0),l.position.set(s.x,s.y,s.z),l.lookAt(s.x+d[M],s.y,s.z)):y===1?(l.up.set(0,0,c[M]),l.position.set(s.x,s.y,s.z),l.lookAt(s.x,s.y+d[M],s.z)):(l.up.set(0,c[M],0),l.position.set(s.x,s.y,s.z),l.lookAt(s.x,s.y,s.z+d[M]));let C=this._cubeSize;Eo(r,y*C,M>2?C:0,C,C),u.setRenderTarget(r),f&&u.render(m,l),u.render(e,l)}m.geometry.dispose(),m.material.dispose(),u.toneMapping=p,u.autoClear=h,e.background=S}_textureToCubeUV(e,t){let n=this._renderer,r=e.mapping===Ai||e.mapping===Ci;r?(this._cubemapMaterial===null&&(this._cubemapMaterial=uu()),this._cubemapMaterial.uniforms.flipEnvMap.value=e.isRenderTargetTexture===!1?-1:1):this._equirectMaterial===null&&(this._equirectMaterial=du());let s=r?this._cubemapMaterial:this._equirectMaterial,a=new st(this._lodPlanes[0],s),o=s.uniforms;o.envMap.value=e;let l=this._cubeSize;Eo(t,0,0,3*l,2*l),n.setRenderTarget(t),n.render(a,Kl)}_applyPMREM(e){let t=this._renderer,n=t.autoClear;t.autoClear=!1;let r=this._lodPlanes.length;for(let s=1;s<r;s++){let a=Math.sqrt(this._sigmas[s]*this._sigmas[s]-this._sigmas[s-1]*this._sigmas[s-1]),o=lu[(r-s-1)%lu.length];this._blur(e,s-1,s,a,o)}t.autoClear=n}_blur(e,t,n,r,s){let a=this._pingPongRenderTarget;this._halfBlur(e,a,t,n,r,"latitudinal",s),this._halfBlur(a,e,n,n,r,"longitudinal",s)}_halfBlur(e,t,n,r,s,a,o){let l=this._renderer,c=this._blurMaterial;a!=="latitudinal"&&a!=="longitudinal"&&console.error("blur direction must be either latitudinal or longitudinal!");let d=3,u=new st(this._lodPlanes[r],c),h=c.uniforms,p=this._sizeLods[n]-1,g=isFinite(s)?Math.PI/(2*p):2*Math.PI/(2*Di-1),x=s/g,m=isFinite(s)?1+Math.floor(d*x):Di;m>Di&&console.warn(`sigmaRadians, ${s}, is too large and will clip, as it requested ${m} samples when the maximum is set to ${Di}`);let f=[],S=0;for(let R=0;R<Di;++R){let P=R/x,w=Math.exp(-P*P/2);f.push(w),R===0?S+=w:R<m&&(S+=2*w)}for(let R=0;R<f.length;R++)f[R]=f[R]/S;h.envMap.value=e.texture,h.samples.value=m,h.weights.value=f,h.latitudinal.value=a==="latitudinal",o&&(h.poleAxis.value=o);let{_lodMax:M}=this;h.dTheta.value=g,h.mipInt.value=M-n;let y=this._sizeLods[r],C=3*y*(r>M-br?r-M+br:0),E=4*(this._cubeSize-y);Eo(t,C,E,3*y,2*y),l.setRenderTarget(t),l.render(u,Kl)}};function cg(i){let e=[],t=[],n=[],r=i,s=i-br+1+au.length;for(let a=0;a<s;a++){let o=Math.pow(2,r);t.push(o);let l=1/o;a>i-br?l=au[a-i+br-1]:a===0&&(l=0),n.push(l);let c=1/(o-2),d=-c,u=1+c,h=[d,d,u,d,u,u,d,d,u,u,d,u],p=6,g=6,x=3,m=2,f=1,S=new Float32Array(x*g*p),M=new Float32Array(m*g*p),y=new Float32Array(f*g*p);for(let E=0;E<p;E++){let R=E%3*2/3-1,P=E>2?0:-1,w=[R,P,0,R+2/3,P,0,R+2/3,P+1,0,R,P,0,R+2/3,P+1,0,R,P+1,0];S.set(w,x*g*E),M.set(h,m*g*E);let v=[E,E,E,E,E,E];y.set(v,f*g*E)}let C=new dt;C.setAttribute("position",new Gt(S,x)),C.setAttribute("uv",new Gt(M,m)),C.setAttribute("faceIndex",new Gt(y,f)),e.push(C),r>br&&r--}return{lodPlanes:e,sizeLods:t,sigmas:n}}function cu(i,e,t){let n=new Cn(i,e,t);return n.texture.mapping=hs,n.texture.name="PMREM.cubeUv",n.scissorTest=!0,n}function Eo(i,e,t,n,r){i.viewport.set(e,t,n,r),i.scissor.set(e,t,n,r)}function dg(i,e,t){let n=new Float32Array(Di),r=new N(0,1,0);return new tn({name:"SphericalGaussianBlur",defines:{n:Di,CUBEUV_TEXEL_WIDTH:1/e,CUBEUV_TEXEL_HEIGHT:1/t,CUBEUV_MAX_MIP:`${i}.0`},uniforms:{envMap:{value:null},samples:{value:1},weights:{value:n},latitudinal:{value:!1},dTheta:{value:0},mipInt:{value:0},poleAxis:{value:r}},vertexShader:uc(),fragmentShader:`

			precision mediump float;
			precision mediump int;

			varying vec3 vOutputDirection;

			uniform sampler2D envMap;
			uniform int samples;
			uniform float weights[ n ];
			uniform bool latitudinal;
			uniform float dTheta;
			uniform float mipInt;
			uniform vec3 poleAxis;

			#define ENVMAP_TYPE_CUBE_UV
			#include <cube_uv_reflection_fragment>

			vec3 getSample( float theta, vec3 axis ) {

				float cosTheta = cos( theta );
				// Rodrigues' axis-angle rotation
				vec3 sampleDirection = vOutputDirection * cosTheta
					+ cross( axis, vOutputDirection ) * sin( theta )
					+ axis * dot( axis, vOutputDirection ) * ( 1.0 - cosTheta );

				return bilinearCubeUV( envMap, sampleDirection, mipInt );

			}

			void main() {

				vec3 axis = latitudinal ? poleAxis : cross( poleAxis, vOutputDirection );

				if ( all( equal( axis, vec3( 0.0 ) ) ) ) {

					axis = vec3( vOutputDirection.z, 0.0, - vOutputDirection.x );

				}

				axis = normalize( axis );

				gl_FragColor = vec4( 0.0, 0.0, 0.0, 1.0 );
				gl_FragColor.rgb += weights[ 0 ] * getSample( 0.0, axis );

				for ( int i = 1; i < n; i++ ) {

					if ( i >= samples ) {

						break;

					}

					float theta = dTheta * float( i );
					gl_FragColor.rgb += weights[ i ] * getSample( -1.0 * theta, axis );
					gl_FragColor.rgb += weights[ i ] * getSample( theta, axis );

				}

			}
		`,blending:Xn,depthTest:!1,depthWrite:!1})}function du(){return new tn({name:"EquirectangularToCubeUV",uniforms:{envMap:{value:null}},vertexShader:uc(),fragmentShader:`

			precision mediump float;
			precision mediump int;

			varying vec3 vOutputDirection;

			uniform sampler2D envMap;

			#include <common>

			void main() {

				vec3 outputDirection = normalize( vOutputDirection );
				vec2 uv = equirectUv( outputDirection );

				gl_FragColor = vec4( texture2D ( envMap, uv ).rgb, 1.0 );

			}
		`,blending:Xn,depthTest:!1,depthWrite:!1})}function uu(){return new tn({name:"CubemapToCubeUV",uniforms:{envMap:{value:null},flipEnvMap:{value:-1}},vertexShader:uc(),fragmentShader:`

			precision mediump float;
			precision mediump int;

			uniform float flipEnvMap;

			varying vec3 vOutputDirection;

			uniform samplerCube envMap;

			void main() {

				gl_FragColor = textureCube( envMap, vec3( flipEnvMap * vOutputDirection.x, vOutputDirection.yz ) );

			}
		`,blending:Xn,depthTest:!1,depthWrite:!1})}function uc(){return`

		precision mediump float;
		precision mediump int;

		attribute float faceIndex;

		varying vec3 vOutputDirection;

		// RH coordinate system; PMREM face-indexing convention
		vec3 getDirection( vec2 uv, float face ) {

			uv = 2.0 * uv - 1.0;

			vec3 direction = vec3( uv, 1.0 );

			if ( face == 0.0 ) {

				direction = direction.zyx; // ( 1, v, u ) pos x

			} else if ( face == 1.0 ) {

				direction = direction.xzy;
				direction.xz *= -1.0; // ( -u, 1, -v ) pos y

			} else if ( face == 2.0 ) {

				direction.x *= -1.0; // ( -u, v, 1 ) pos z

			} else if ( face == 3.0 ) {

				direction = direction.zyx;
				direction.xz *= -1.0; // ( -1, v, -u ) neg x

			} else if ( face == 4.0 ) {

				direction = direction.xzy;
				direction.xy *= -1.0; // ( -u, -1, v ) neg y

			} else if ( face == 5.0 ) {

				direction.z *= -1.0; // ( u, v, -1 ) neg z

			}

			return direction;

		}

		void main() {

			vOutputDirection = getDirection( uv, faceIndex );
			gl_Position = vec4( position, 1.0 );

		}
	`}function ug(i){let e=new WeakMap,t=null;function n(o){if(o&&o.isTexture){let l=o.mapping,c=l===ka||l===Ha,d=l===Ai||l===Ci;if(c||d){let u=e.get(o),h=u!==void 0?u.texture.pmremVersion:0;if(o.isRenderTargetTexture&&o.pmremVersion!==h)return t===null&&(t=new Ao(i)),u=c?t.fromEquirectangular(o,u):t.fromCubemap(o,u),u.texture.pmremVersion=o.pmremVersion,e.set(o,u),u.texture;if(u!==void 0)return u.texture;{let p=o.image;return c&&p&&p.height>0||d&&p&&r(p)?(t===null&&(t=new Ao(i)),u=c?t.fromEquirectangular(o):t.fromCubemap(o),u.texture.pmremVersion=o.pmremVersion,e.set(o,u),o.addEventListener("dispose",s),u.texture):null}}}return o}function r(o){let l=0,c=6;for(let d=0;d<c;d++)o[d]!==void 0&&l++;return l===c}function s(o){let l=o.target;l.removeEventListener("dispose",s);let c=e.get(l);c!==void 0&&(e.delete(l),c.dispose())}function a(){e=new WeakMap,t!==null&&(t.dispose(),t=null)}return{get:n,dispose:a}}function hg(i){let e={};function t(n){if(e[n]!==void 0)return e[n];let r;switch(n){case"WEBGL_depth_texture":r=i.getExtension("WEBGL_depth_texture")||i.getExtension("MOZ_WEBGL_depth_texture")||i.getExtension("WEBKIT_WEBGL_depth_texture");break;case"EXT_texture_filter_anisotropic":r=i.getExtension("EXT_texture_filter_anisotropic")||i.getExtension("MOZ_EXT_texture_filter_anisotropic")||i.getExtension("WEBKIT_EXT_texture_filter_anisotropic");break;case"WEBGL_compressed_texture_s3tc":r=i.getExtension("WEBGL_compressed_texture_s3tc")||i.getExtension("MOZ_WEBGL_compressed_texture_s3tc")||i.getExtension("WEBKIT_WEBGL_compressed_texture_s3tc");break;case"WEBGL_compressed_texture_pvrtc":r=i.getExtension("WEBGL_compressed_texture_pvrtc")||i.getExtension("WEBKIT_WEBGL_compressed_texture_pvrtc");break;default:r=i.getExtension(n)}return e[n]=r,r}return{has:function(n){return t(n)!==null},init:function(){t("EXT_color_buffer_float"),t("WEBGL_clip_cull_distance"),t("OES_texture_float_linear"),t("EXT_color_buffer_half_float"),t("WEBGL_multisampled_render_to_texture"),t("WEBGL_render_shared_exponent")},get:function(n){let r=t(n);return r===null&&cr("THREE.WebGLRenderer: "+n+" extension not supported."),r}}}function fg(i,e,t,n){let r={},s=new WeakMap;function a(u){let h=u.target;h.index!==null&&e.remove(h.index);for(let g in h.attributes)e.remove(h.attributes[g]);h.removeEventListener("dispose",a),delete r[h.id];let p=s.get(h);p&&(e.remove(p),s.delete(h)),n.releaseStatesOfGeometry(h),h.isInstancedBufferGeometry===!0&&delete h._maxInstanceCount,t.memory.geometries--}function o(u,h){return r[h.id]===!0||(h.addEventListener("dispose",a),r[h.id]=!0,t.memory.geometries++),h}function l(u){let h=u.attributes;for(let p in h)e.update(h[p],i.ARRAY_BUFFER)}function c(u){let h=[],p=u.index,g=u.attributes.position,x=0;if(p!==null){let S=p.array;x=p.version;for(let M=0,y=S.length;M<y;M+=3){let C=S[M+0],E=S[M+1],R=S[M+2];h.push(C,E,E,R,R,C)}}else if(g!==void 0){let S=g.array;x=g.version;for(let M=0,y=S.length/3-1;M<y;M+=3){let C=M+0,E=M+1,R=M+2;h.push(C,E,E,R,R,C)}}else return;let m=new($l(h)?$r:Xr)(h,1);m.version=x;let f=s.get(u);f&&e.remove(f),s.set(u,m)}function d(u){let h=s.get(u);if(h){let p=u.index;p!==null&&h.version<p.version&&c(u)}else c(u);return s.get(u)}return{get:o,update:l,getWireframeAttribute:d}}function pg(i,e,t){let n;function r(h){n=h}let s,a;function o(h){s=h.type,a=h.bytesPerElement}function l(h,p){i.drawElements(n,p,s,h*a),t.update(p,n,1)}function c(h,p,g){g!==0&&(i.drawElementsInstanced(n,p,s,h*a,g),t.update(p,n,g))}function d(h,p,g){if(g===0)return;e.get("WEBGL_multi_draw").multiDrawElementsWEBGL(n,p,0,s,h,0,g);let m=0;for(let f=0;f<g;f++)m+=p[f];t.update(m,n,1)}function u(h,p,g,x){if(g===0)return;let m=e.get("WEBGL_multi_draw");if(m===null)for(let f=0;f<h.length;f++)c(h[f]/a,p[f],x[f]);else{m.multiDrawElementsInstancedWEBGL(n,p,0,s,h,0,x,0,g);let f=0;for(let S=0;S<g;S++)f+=p[S]*x[S];t.update(f,n,1)}}this.setMode=r,this.setIndex=o,this.render=l,this.renderInstances=c,this.renderMultiDraw=d,this.renderMultiDrawInstances=u}function mg(i){let e={geometries:0,textures:0},t={frame:0,calls:0,triangles:0,points:0,lines:0};function n(s,a,o){switch(t.calls++,a){case i.TRIANGLES:t.triangles+=o*(s/3);break;case i.LINES:t.lines+=o*(s/2);break;case i.LINE_STRIP:t.lines+=o*(s-1);break;case i.LINE_LOOP:t.lines+=o*s;break;case i.POINTS:t.points+=o*s;break;default:console.error("THREE.WebGLInfo: Unknown draw mode:",a);break}}function r(){t.calls=0,t.triangles=0,t.points=0,t.lines=0}return{memory:e,render:t,programs:null,autoReset:!0,reset:r,update:n}}function gg(i,e,t){let n=new WeakMap,r=new pt;function s(a,o,l){let c=a.morphTargetInfluences,d=o.morphAttributes.position||o.morphAttributes.normal||o.morphAttributes.color,u=d!==void 0?d.length:0,h=n.get(o);if(h===void 0||h.count!==u){let w=function(){R.dispose(),n.delete(o),o.removeEventListener("dispose",w)};h!==void 0&&h.texture.dispose();let p=o.morphAttributes.position!==void 0,g=o.morphAttributes.normal!==void 0,x=o.morphAttributes.color!==void 0,m=o.morphAttributes.position||[],f=o.morphAttributes.normal||[],S=o.morphAttributes.color||[],M=0;p===!0&&(M=1),g===!0&&(M=2),x===!0&&(M=3);let y=o.attributes.position.count*M,C=1;y>e.maxTextureSize&&(C=Math.ceil(y/e.maxTextureSize),y=e.maxTextureSize);let E=new Float32Array(y*C*4*u),R=new Gr(E,y,C,u);R.type=Pn,R.needsUpdate=!0;let P=M*4;for(let v=0;v<u;v++){let T=m[v],D=f[v],F=S[v],B=y*C*4*v;for(let k=0;k<T.count;k++){let W=k*P;p===!0&&(r.fromBufferAttribute(T,k),E[B+W+0]=r.x,E[B+W+1]=r.y,E[B+W+2]=r.z,E[B+W+3]=0),g===!0&&(r.fromBufferAttribute(D,k),E[B+W+4]=r.x,E[B+W+5]=r.y,E[B+W+6]=r.z,E[B+W+7]=0),x===!0&&(r.fromBufferAttribute(F,k),E[B+W+8]=r.x,E[B+W+9]=r.y,E[B+W+10]=r.z,E[B+W+11]=F.itemSize===4?r.w:1)}}h={count:u,texture:R,size:new He(y,C)},n.set(o,h),o.addEventListener("dispose",w)}if(a.isInstancedMesh===!0&&a.morphTexture!==null)l.getUniforms().setValue(i,"morphTexture",a.morphTexture,t);else{let p=0;for(let x=0;x<c.length;x++)p+=c[x];let g=o.morphTargetsRelative?1:1-p;l.getUniforms().setValue(i,"morphTargetBaseInfluence",g),l.getUniforms().setValue(i,"morphTargetInfluences",c)}l.getUniforms().setValue(i,"morphTargetsTexture",h.texture,t),l.getUniforms().setValue(i,"morphTargetsTextureSize",h.size)}return{update:s}}function xg(i,e,t,n){let r=new WeakMap;function s(l){let c=n.render.frame,d=l.geometry,u=e.get(l,d);if(r.get(u)!==c&&(e.update(u),r.set(u,c)),l.isInstancedMesh&&(l.hasEventListener("dispose",o)===!1&&l.addEventListener("dispose",o),r.get(l)!==c&&(t.update(l.instanceMatrix,i.ARRAY_BUFFER),l.instanceColor!==null&&t.update(l.instanceColor,i.ARRAY_BUFFER),r.set(l,c))),l.isSkinnedMesh){let h=l.skeleton;r.get(h)!==c&&(h.update(),r.set(h,c))}return u}function a(){r=new WeakMap}function o(l){let c=l.target;c.removeEventListener("dispose",o),t.remove(c.instanceMatrix),c.instanceColor!==null&&t.remove(c.instanceColor)}return{update:s,dispose:a}}var Iu=new Lt,hu=new es(1,1),Pu=new Gr,Nu=new pa,Du=new Yr,fu=[],pu=[],mu=new Float32Array(16),gu=new Float32Array(9),xu=new Float32Array(4);function Mr(i,e,t){let n=i[0];if(n<=0||n>0)return i;let r=e*t,s=fu[r];if(s===void 0&&(s=new Float32Array(r),fu[r]=s),e!==0){n.toArray(s,0);for(let a=1,o=0;a!==e;++a)o+=t,i[a].toArray(s,o)}return s}function St(i,e){if(i.length!==e.length)return!1;for(let t=0,n=i.length;t<n;t++)if(i[t]!==e[t])return!1;return!0}function Et(i,e){for(let t=0,n=e.length;t<n;t++)i[t]=e[t]}function Ro(i,e){let t=pu[e];t===void 0&&(t=new Int32Array(e),pu[e]=t);for(let n=0;n!==e;++n)t[n]=i.allocateTextureUnit();return t}function _g(i,e){let t=this.cache;t[0]!==e&&(i.uniform1f(this.addr,e),t[0]=e)}function yg(i,e){let t=this.cache;if(e.x!==void 0)(t[0]!==e.x||t[1]!==e.y)&&(i.uniform2f(this.addr,e.x,e.y),t[0]=e.x,t[1]=e.y);else{if(St(t,e))return;i.uniform2fv(this.addr,e),Et(t,e)}}function vg(i,e){let t=this.cache;if(e.x!==void 0)(t[0]!==e.x||t[1]!==e.y||t[2]!==e.z)&&(i.uniform3f(this.addr,e.x,e.y,e.z),t[0]=e.x,t[1]=e.y,t[2]=e.z);else if(e.r!==void 0)(t[0]!==e.r||t[1]!==e.g||t[2]!==e.b)&&(i.uniform3f(this.addr,e.r,e.g,e.b),t[0]=e.r,t[1]=e.g,t[2]=e.b);else{if(St(t,e))return;i.uniform3fv(this.addr,e),Et(t,e)}}function bg(i,e){let t=this.cache;if(e.x!==void 0)(t[0]!==e.x||t[1]!==e.y||t[2]!==e.z||t[3]!==e.w)&&(i.uniform4f(this.addr,e.x,e.y,e.z,e.w),t[0]=e.x,t[1]=e.y,t[2]=e.z,t[3]=e.w);else{if(St(t,e))return;i.uniform4fv(this.addr,e),Et(t,e)}}function wg(i,e){let t=this.cache,n=e.elements;if(n===void 0){if(St(t,e))return;i.uniformMatrix2fv(this.addr,!1,e),Et(t,e)}else{if(St(t,n))return;xu.set(n),i.uniformMatrix2fv(this.addr,!1,xu),Et(t,n)}}function Mg(i,e){let t=this.cache,n=e.elements;if(n===void 0){if(St(t,e))return;i.uniformMatrix3fv(this.addr,!1,e),Et(t,e)}else{if(St(t,n))return;gu.set(n),i.uniformMatrix3fv(this.addr,!1,gu),Et(t,n)}}function Sg(i,e){let t=this.cache,n=e.elements;if(n===void 0){if(St(t,e))return;i.uniformMatrix4fv(this.addr,!1,e),Et(t,e)}else{if(St(t,n))return;mu.set(n),i.uniformMatrix4fv(this.addr,!1,mu),Et(t,n)}}function Eg(i,e){let t=this.cache;t[0]!==e&&(i.uniform1i(this.addr,e),t[0]=e)}function Tg(i,e){let t=this.cache;if(e.x!==void 0)(t[0]!==e.x||t[1]!==e.y)&&(i.uniform2i(this.addr,e.x,e.y),t[0]=e.x,t[1]=e.y);else{if(St(t,e))return;i.uniform2iv(this.addr,e),Et(t,e)}}function Ag(i,e){let t=this.cache;if(e.x!==void 0)(t[0]!==e.x||t[1]!==e.y||t[2]!==e.z)&&(i.uniform3i(this.addr,e.x,e.y,e.z),t[0]=e.x,t[1]=e.y,t[2]=e.z);else{if(St(t,e))return;i.uniform3iv(this.addr,e),Et(t,e)}}function Cg(i,e){let t=this.cache;if(e.x!==void 0)(t[0]!==e.x||t[1]!==e.y||t[2]!==e.z||t[3]!==e.w)&&(i.uniform4i(this.addr,e.x,e.y,e.z,e.w),t[0]=e.x,t[1]=e.y,t[2]=e.z,t[3]=e.w);else{if(St(t,e))return;i.uniform4iv(this.addr,e),Et(t,e)}}function Rg(i,e){let t=this.cache;t[0]!==e&&(i.uniform1ui(this.addr,e),t[0]=e)}function Ig(i,e){let t=this.cache;if(e.x!==void 0)(t[0]!==e.x||t[1]!==e.y)&&(i.uniform2ui(this.addr,e.x,e.y),t[0]=e.x,t[1]=e.y);else{if(St(t,e))return;i.uniform2uiv(this.addr,e),Et(t,e)}}function Pg(i,e){let t=this.cache;if(e.x!==void 0)(t[0]!==e.x||t[1]!==e.y||t[2]!==e.z)&&(i.uniform3ui(this.addr,e.x,e.y,e.z),t[0]=e.x,t[1]=e.y,t[2]=e.z);else{if(St(t,e))return;i.uniform3uiv(this.addr,e),Et(t,e)}}function Ng(i,e){let t=this.cache;if(e.x!==void 0)(t[0]!==e.x||t[1]!==e.y||t[2]!==e.z||t[3]!==e.w)&&(i.uniform4ui(this.addr,e.x,e.y,e.z,e.w),t[0]=e.x,t[1]=e.y,t[2]=e.z,t[3]=e.w);else{if(St(t,e))return;i.uniform4uiv(this.addr,e),Et(t,e)}}function Dg(i,e,t){let n=this.cache,r=t.allocateTextureUnit();n[0]!==r&&(i.uniform1i(this.addr,r),n[0]=r);let s;this.type===i.SAMPLER_2D_SHADOW?(hu.compareFunction=Gl,s=hu):s=Iu,t.setTexture2D(e||s,r)}function Lg(i,e,t){let n=this.cache,r=t.allocateTextureUnit();n[0]!==r&&(i.uniform1i(this.addr,r),n[0]=r),t.setTexture3D(e||Nu,r)}function Fg(i,e,t){let n=this.cache,r=t.allocateTextureUnit();n[0]!==r&&(i.uniform1i(this.addr,r),n[0]=r),t.setTextureCube(e||Du,r)}function Ug(i,e,t){let n=this.cache,r=t.allocateTextureUnit();n[0]!==r&&(i.uniform1i(this.addr,r),n[0]=r),t.setTexture2DArray(e||Pu,r)}function Og(i){switch(i){case 5126:return _g;case 35664:return yg;case 35665:return vg;case 35666:return bg;case 35674:return wg;case 35675:return Mg;case 35676:return Sg;case 5124:case 35670:return Eg;case 35667:case 35671:return Tg;case 35668:case 35672:return Ag;case 35669:case 35673:return Cg;case 5125:return Rg;case 36294:return Ig;case 36295:return Pg;case 36296:return Ng;case 35678:case 36198:case 36298:case 36306:case 35682:return Dg;case 35679:case 36299:case 36307:return Lg;case 35680:case 36300:case 36308:case 36293:return Fg;case 36289:case 36303:case 36311:case 36292:return Ug}}function Bg(i,e){i.uniform1fv(this.addr,e)}function zg(i,e){let t=Mr(e,this.size,2);i.uniform2fv(this.addr,t)}function kg(i,e){let t=Mr(e,this.size,3);i.uniform3fv(this.addr,t)}function Hg(i,e){let t=Mr(e,this.size,4);i.uniform4fv(this.addr,t)}function Vg(i,e){let t=Mr(e,this.size,4);i.uniformMatrix2fv(this.addr,!1,t)}function Gg(i,e){let t=Mr(e,this.size,9);i.uniformMatrix3fv(this.addr,!1,t)}function Wg(i,e){let t=Mr(e,this.size,16);i.uniformMatrix4fv(this.addr,!1,t)}function Xg(i,e){i.uniform1iv(this.addr,e)}function $g(i,e){i.uniform2iv(this.addr,e)}function qg(i,e){i.uniform3iv(this.addr,e)}function Yg(i,e){i.uniform4iv(this.addr,e)}function Zg(i,e){i.uniform1uiv(this.addr,e)}function Jg(i,e){i.uniform2uiv(this.addr,e)}function Kg(i,e){i.uniform3uiv(this.addr,e)}function jg(i,e){i.uniform4uiv(this.addr,e)}function Qg(i,e,t){let n=this.cache,r=e.length,s=Ro(t,r);St(n,s)||(i.uniform1iv(this.addr,s),Et(n,s));for(let a=0;a!==r;++a)t.setTexture2D(e[a]||Iu,s[a])}function e0(i,e,t){let n=this.cache,r=e.length,s=Ro(t,r);St(n,s)||(i.uniform1iv(this.addr,s),Et(n,s));for(let a=0;a!==r;++a)t.setTexture3D(e[a]||Nu,s[a])}function t0(i,e,t){let n=this.cache,r=e.length,s=Ro(t,r);St(n,s)||(i.uniform1iv(this.addr,s),Et(n,s));for(let a=0;a!==r;++a)t.setTextureCube(e[a]||Du,s[a])}function n0(i,e,t){let n=this.cache,r=e.length,s=Ro(t,r);St(n,s)||(i.uniform1iv(this.addr,s),Et(n,s));for(let a=0;a!==r;++a)t.setTexture2DArray(e[a]||Pu,s[a])}function i0(i){switch(i){case 5126:return Bg;case 35664:return zg;case 35665:return kg;case 35666:return Hg;case 35674:return Vg;case 35675:return Gg;case 35676:return Wg;case 5124:case 35670:return Xg;case 35667:case 35671:return $g;case 35668:case 35672:return qg;case 35669:case 35673:return Yg;case 5125:return Zg;case 36294:return Jg;case 36295:return Kg;case 36296:return jg;case 35678:case 36198:case 36298:case 36306:case 35682:return Qg;case 35679:case 36299:case 36307:return e0;case 35680:case 36300:case 36308:case 36293:return t0;case 36289:case 36303:case 36311:case 36292:return n0}}var ic=class{constructor(e,t,n){this.id=e,this.addr=n,this.cache=[],this.type=t.type,this.setValue=Og(t.type)}},rc=class{constructor(e,t,n){this.id=e,this.addr=n,this.cache=[],this.type=t.type,this.size=t.size,this.setValue=i0(t.type)}},sc=class{constructor(e){this.id=e,this.seq=[],this.map={}}setValue(e,t,n){let r=this.seq;for(let s=0,a=r.length;s!==a;++s){let o=r[s];o.setValue(e,t[o.id],n)}}},nc=/(\w+)(\])?(\[|\.)?/g;function _u(i,e){i.seq.push(e),i.map[e.id]=e}function r0(i,e,t){let n=i.name,r=n.length;for(nc.lastIndex=0;;){let s=nc.exec(n),a=nc.lastIndex,o=s[1],l=s[2]==="]",c=s[3];if(l&&(o=o|0),c===void 0||c==="["&&a+2===r){_u(t,c===void 0?new ic(o,i,e):new rc(o,i,e));break}else{let u=t.map[o];u===void 0&&(u=new sc(o),_u(t,u)),t=u}}}var wr=class{constructor(e,t){this.seq=[],this.map={};let n=e.getProgramParameter(t,e.ACTIVE_UNIFORMS);for(let r=0;r<n;++r){let s=e.getActiveUniform(t,r),a=e.getUniformLocation(t,s.name);r0(s,a,this)}}setValue(e,t,n,r){let s=this.map[t];s!==void 0&&s.setValue(e,n,r)}setOptional(e,t,n){let r=t[n];r!==void 0&&this.setValue(e,n,r)}static upload(e,t,n,r){for(let s=0,a=t.length;s!==a;++s){let o=t[s],l=n[o.id];l.needsUpdate!==!1&&o.setValue(e,l.value,r)}}static seqWithValue(e,t){let n=[];for(let r=0,s=e.length;r!==s;++r){let a=e[r];a.id in t&&n.push(a)}return n}};function yu(i,e,t){let n=i.createShader(e);return i.shaderSource(n,t),i.compileShader(n),n}var s0=37297,a0=0;function o0(i,e){let t=i.split(`
`),n=[],r=Math.max(e-6,0),s=Math.min(e+6,t.length);for(let a=r;a<s;a++){let o=a+1;n.push(`${o===e?">":" "} ${o}: ${t[a]}`)}return n.join(`
`)}var vu=new Oe;function l0(i){$e._getMatrix(vu,$e.workingColorSpace,i);let e=`mat3( ${vu.elements.map(t=>t.toFixed(4))} )`;switch($e.getTransfer(i)){case kr:return[e,"LinearTransferOETF"];case Ke:return[e,"sRGBTransferOETF"];default:return console.warn("THREE.WebGLProgram: Unsupported color space: ",i),[e,"LinearTransferOETF"]}}function bu(i,e,t){let n=i.getShaderParameter(e,i.COMPILE_STATUS),s=(i.getShaderInfoLog(e)||"").trim();if(n&&s==="")return"";let a=/ERROR: 0:(\d+)/.exec(s);if(a){let o=parseInt(a[1]);return t.toUpperCase()+`

`+s+`

`+o0(i.getShaderSource(e),o)}else return s}function c0(i,e){let t=l0(e);return[`vec4 ${i}( vec4 value ) {`,`	return ${t[1]}( vec4( value.rgb * ${t[0]}, value.a ) );`,"}"].join(`
`)}function d0(i,e){let t;switch(e){case Ud:t="Linear";break;case Od:t="Reinhard";break;case Bd:t="Cineon";break;case zd:t="ACESFilmic";break;case Hd:t="AgX";break;case Vd:t="Neutral";break;case kd:t="Custom";break;default:console.warn("THREE.WebGLProgram: Unsupported toneMapping:",e),t="Linear"}return"vec3 "+i+"( vec3 color ) { return "+t+"ToneMapping( color ); }"}var To=new N;function u0(){$e.getLuminanceCoefficients(To);let i=To.x.toFixed(4),e=To.y.toFixed(4),t=To.z.toFixed(4);return["float luminance( const in vec3 rgb ) {",`	const vec3 weights = vec3( ${i}, ${e}, ${t} );`,"	return dot( weights, rgb );","}"].join(`
`)}function h0(i){return[i.extensionClipCullDistance?"#extension GL_ANGLE_clip_cull_distance : require":"",i.extensionMultiDraw?"#extension GL_ANGLE_multi_draw : require":""].filter(_s).join(`
`)}function f0(i){let e=[];for(let t in i){let n=i[t];n!==!1&&e.push("#define "+t+" "+n)}return e.join(`
`)}function p0(i,e){let t={},n=i.getProgramParameter(e,i.ACTIVE_ATTRIBUTES);for(let r=0;r<n;r++){let s=i.getActiveAttrib(e,r),a=s.name,o=1;s.type===i.FLOAT_MAT2&&(o=2),s.type===i.FLOAT_MAT3&&(o=3),s.type===i.FLOAT_MAT4&&(o=4),t[a]={type:s.type,location:i.getAttribLocation(e,a),locationSize:o}}return t}function _s(i){return i!==""}function wu(i,e){let t=e.numSpotLightShadows+e.numSpotLightMaps-e.numSpotLightShadowsWithMaps;return i.replace(/NUM_DIR_LIGHTS/g,e.numDirLights).replace(/NUM_SPOT_LIGHTS/g,e.numSpotLights).replace(/NUM_SPOT_LIGHT_MAPS/g,e.numSpotLightMaps).replace(/NUM_SPOT_LIGHT_COORDS/g,t).replace(/NUM_RECT_AREA_LIGHTS/g,e.numRectAreaLights).replace(/NUM_POINT_LIGHTS/g,e.numPointLights).replace(/NUM_HEMI_LIGHTS/g,e.numHemiLights).replace(/NUM_DIR_LIGHT_SHADOWS/g,e.numDirLightShadows).replace(/NUM_SPOT_LIGHT_SHADOWS_WITH_MAPS/g,e.numSpotLightShadowsWithMaps).replace(/NUM_SPOT_LIGHT_SHADOWS/g,e.numSpotLightShadows).replace(/NUM_POINT_LIGHT_SHADOWS/g,e.numPointLightShadows)}function Mu(i,e){return i.replace(/NUM_CLIPPING_PLANES/g,e.numClippingPlanes).replace(/UNION_CLIPPING_PLANES/g,e.numClippingPlanes-e.numClipIntersection)}var m0=/^[ \t]*#include +<([\w\d./]+)>/gm;function ac(i){return i.replace(m0,x0)}var g0=new Map;function x0(i,e){let t=Ve[e];if(t===void 0){let n=g0.get(e);if(n!==void 0)t=Ve[n],console.warn('THREE.WebGLRenderer: Shader chunk "%s" has been deprecated. Use "%s" instead.',e,n);else throw new Error("Can not resolve #include <"+e+">")}return ac(t)}var _0=/#pragma unroll_loop_start\s+for\s*\(\s*int\s+i\s*=\s*(\d+)\s*;\s*i\s*<\s*(\d+)\s*;\s*i\s*\+\+\s*\)\s*{([\s\S]+?)}\s+#pragma unroll_loop_end/g;function Su(i){return i.replace(_0,y0)}function y0(i,e,t,n){let r="";for(let s=parseInt(e);s<parseInt(t);s++)r+=n.replace(/\[\s*i\s*\]/g,"[ "+s+" ]").replace(/UNROLLED_LOOP_INDEX/g,s);return r}function Eu(i){let e=`precision ${i.precision} float;
	precision ${i.precision} int;
	precision ${i.precision} sampler2D;
	precision ${i.precision} samplerCube;
	precision ${i.precision} sampler3D;
	precision ${i.precision} sampler2DArray;
	precision ${i.precision} sampler2DShadow;
	precision ${i.precision} samplerCubeShadow;
	precision ${i.precision} sampler2DArrayShadow;
	precision ${i.precision} isampler2D;
	precision ${i.precision} isampler3D;
	precision ${i.precision} isamplerCube;
	precision ${i.precision} isampler2DArray;
	precision ${i.precision} usampler2D;
	precision ${i.precision} usampler3D;
	precision ${i.precision} usamplerCube;
	precision ${i.precision} usampler2DArray;
	`;return i.precision==="highp"?e+=`
#define HIGH_PRECISION`:i.precision==="mediump"?e+=`
#define MEDIUM_PRECISION`:i.precision==="lowp"&&(e+=`
#define LOW_PRECISION`),e}function v0(i){let e="SHADOWMAP_TYPE_BASIC";return i.shadowMapType===Cl?e="SHADOWMAP_TYPE_PCF":i.shadowMapType===md?e="SHADOWMAP_TYPE_PCF_SOFT":i.shadowMapType===In&&(e="SHADOWMAP_TYPE_VSM"),e}function b0(i){let e="ENVMAP_TYPE_CUBE";if(i.envMap)switch(i.envMapMode){case Ai:case Ci:e="ENVMAP_TYPE_CUBE";break;case hs:e="ENVMAP_TYPE_CUBE_UV";break}return e}function w0(i){let e="ENVMAP_MODE_REFLECTION";if(i.envMap)switch(i.envMapMode){case Ci:e="ENVMAP_MODE_REFRACTION";break}return e}function M0(i){let e="ENVMAP_BLENDING_NONE";if(i.envMap)switch(i.combine){case Nl:e="ENVMAP_BLENDING_MULTIPLY";break;case Ld:e="ENVMAP_BLENDING_MIX";break;case Fd:e="ENVMAP_BLENDING_ADD";break}return e}function S0(i){let e=i.envMapCubeUVHeight;if(e===null)return null;let t=Math.log2(e)-2,n=1/e;return{texelWidth:1/(3*Math.max(Math.pow(2,t),112)),texelHeight:n,maxMip:t}}function E0(i,e,t,n){let r=i.getContext(),s=t.defines,a=t.vertexShader,o=t.fragmentShader,l=v0(t),c=b0(t),d=w0(t),u=M0(t),h=S0(t),p=h0(t),g=f0(s),x=r.createProgram(),m,f,S=t.glslVersion?"#version "+t.glslVersion+`
`:"";t.isRawShaderMaterial?(m=["#define SHADER_TYPE "+t.shaderType,"#define SHADER_NAME "+t.shaderName,g].filter(_s).join(`
`),m.length>0&&(m+=`
`),f=["#define SHADER_TYPE "+t.shaderType,"#define SHADER_NAME "+t.shaderName,g].filter(_s).join(`
`),f.length>0&&(f+=`
`)):(m=[Eu(t),"#define SHADER_TYPE "+t.shaderType,"#define SHADER_NAME "+t.shaderName,g,t.extensionClipCullDistance?"#define USE_CLIP_DISTANCE":"",t.batching?"#define USE_BATCHING":"",t.batchingColor?"#define USE_BATCHING_COLOR":"",t.instancing?"#define USE_INSTANCING":"",t.instancingColor?"#define USE_INSTANCING_COLOR":"",t.instancingMorph?"#define USE_INSTANCING_MORPH":"",t.useFog&&t.fog?"#define USE_FOG":"",t.useFog&&t.fogExp2?"#define FOG_EXP2":"",t.map?"#define USE_MAP":"",t.envMap?"#define USE_ENVMAP":"",t.envMap?"#define "+d:"",t.lightMap?"#define USE_LIGHTMAP":"",t.aoMap?"#define USE_AOMAP":"",t.bumpMap?"#define USE_BUMPMAP":"",t.normalMap?"#define USE_NORMALMAP":"",t.normalMapObjectSpace?"#define USE_NORMALMAP_OBJECTSPACE":"",t.normalMapTangentSpace?"#define USE_NORMALMAP_TANGENTSPACE":"",t.displacementMap?"#define USE_DISPLACEMENTMAP":"",t.emissiveMap?"#define USE_EMISSIVEMAP":"",t.anisotropy?"#define USE_ANISOTROPY":"",t.anisotropyMap?"#define USE_ANISOTROPYMAP":"",t.clearcoatMap?"#define USE_CLEARCOATMAP":"",t.clearcoatRoughnessMap?"#define USE_CLEARCOAT_ROUGHNESSMAP":"",t.clearcoatNormalMap?"#define USE_CLEARCOAT_NORMALMAP":"",t.iridescenceMap?"#define USE_IRIDESCENCEMAP":"",t.iridescenceThicknessMap?"#define USE_IRIDESCENCE_THICKNESSMAP":"",t.specularMap?"#define USE_SPECULARMAP":"",t.specularColorMap?"#define USE_SPECULAR_COLORMAP":"",t.specularIntensityMap?"#define USE_SPECULAR_INTENSITYMAP":"",t.roughnessMap?"#define USE_ROUGHNESSMAP":"",t.metalnessMap?"#define USE_METALNESSMAP":"",t.alphaMap?"#define USE_ALPHAMAP":"",t.alphaHash?"#define USE_ALPHAHASH":"",t.transmission?"#define USE_TRANSMISSION":"",t.transmissionMap?"#define USE_TRANSMISSIONMAP":"",t.thicknessMap?"#define USE_THICKNESSMAP":"",t.sheenColorMap?"#define USE_SHEEN_COLORMAP":"",t.sheenRoughnessMap?"#define USE_SHEEN_ROUGHNESSMAP":"",t.mapUv?"#define MAP_UV "+t.mapUv:"",t.alphaMapUv?"#define ALPHAMAP_UV "+t.alphaMapUv:"",t.lightMapUv?"#define LIGHTMAP_UV "+t.lightMapUv:"",t.aoMapUv?"#define AOMAP_UV "+t.aoMapUv:"",t.emissiveMapUv?"#define EMISSIVEMAP_UV "+t.emissiveMapUv:"",t.bumpMapUv?"#define BUMPMAP_UV "+t.bumpMapUv:"",t.normalMapUv?"#define NORMALMAP_UV "+t.normalMapUv:"",t.displacementMapUv?"#define DISPLACEMENTMAP_UV "+t.displacementMapUv:"",t.metalnessMapUv?"#define METALNESSMAP_UV "+t.metalnessMapUv:"",t.roughnessMapUv?"#define ROUGHNESSMAP_UV "+t.roughnessMapUv:"",t.anisotropyMapUv?"#define ANISOTROPYMAP_UV "+t.anisotropyMapUv:"",t.clearcoatMapUv?"#define CLEARCOATMAP_UV "+t.clearcoatMapUv:"",t.clearcoatNormalMapUv?"#define CLEARCOAT_NORMALMAP_UV "+t.clearcoatNormalMapUv:"",t.clearcoatRoughnessMapUv?"#define CLEARCOAT_ROUGHNESSMAP_UV "+t.clearcoatRoughnessMapUv:"",t.iridescenceMapUv?"#define IRIDESCENCEMAP_UV "+t.iridescenceMapUv:"",t.iridescenceThicknessMapUv?"#define IRIDESCENCE_THICKNESSMAP_UV "+t.iridescenceThicknessMapUv:"",t.sheenColorMapUv?"#define SHEEN_COLORMAP_UV "+t.sheenColorMapUv:"",t.sheenRoughnessMapUv?"#define SHEEN_ROUGHNESSMAP_UV "+t.sheenRoughnessMapUv:"",t.specularMapUv?"#define SPECULARMAP_UV "+t.specularMapUv:"",t.specularColorMapUv?"#define SPECULAR_COLORMAP_UV "+t.specularColorMapUv:"",t.specularIntensityMapUv?"#define SPECULAR_INTENSITYMAP_UV "+t.specularIntensityMapUv:"",t.transmissionMapUv?"#define TRANSMISSIONMAP_UV "+t.transmissionMapUv:"",t.thicknessMapUv?"#define THICKNESSMAP_UV "+t.thicknessMapUv:"",t.vertexTangents&&t.flatShading===!1?"#define USE_TANGENT":"",t.vertexColors?"#define USE_COLOR":"",t.vertexAlphas?"#define USE_COLOR_ALPHA":"",t.vertexUv1s?"#define USE_UV1":"",t.vertexUv2s?"#define USE_UV2":"",t.vertexUv3s?"#define USE_UV3":"",t.pointsUvs?"#define USE_POINTS_UV":"",t.flatShading?"#define FLAT_SHADED":"",t.skinning?"#define USE_SKINNING":"",t.morphTargets?"#define USE_MORPHTARGETS":"",t.morphNormals&&t.flatShading===!1?"#define USE_MORPHNORMALS":"",t.morphColors?"#define USE_MORPHCOLORS":"",t.morphTargetsCount>0?"#define MORPHTARGETS_TEXTURE_STRIDE "+t.morphTextureStride:"",t.morphTargetsCount>0?"#define MORPHTARGETS_COUNT "+t.morphTargetsCount:"",t.doubleSided?"#define DOUBLE_SIDED":"",t.flipSided?"#define FLIP_SIDED":"",t.shadowMapEnabled?"#define USE_SHADOWMAP":"",t.shadowMapEnabled?"#define "+l:"",t.sizeAttenuation?"#define USE_SIZEATTENUATION":"",t.numLightProbes>0?"#define USE_LIGHT_PROBES":"",t.logarithmicDepthBuffer?"#define USE_LOGARITHMIC_DEPTH_BUFFER":"",t.reversedDepthBuffer?"#define USE_REVERSED_DEPTH_BUFFER":"","uniform mat4 modelMatrix;","uniform mat4 modelViewMatrix;","uniform mat4 projectionMatrix;","uniform mat4 viewMatrix;","uniform mat3 normalMatrix;","uniform vec3 cameraPosition;","uniform bool isOrthographic;","#ifdef USE_INSTANCING","	attribute mat4 instanceMatrix;","#endif","#ifdef USE_INSTANCING_COLOR","	attribute vec3 instanceColor;","#endif","#ifdef USE_INSTANCING_MORPH","	uniform sampler2D morphTexture;","#endif","attribute vec3 position;","attribute vec3 normal;","attribute vec2 uv;","#ifdef USE_UV1","	attribute vec2 uv1;","#endif","#ifdef USE_UV2","	attribute vec2 uv2;","#endif","#ifdef USE_UV3","	attribute vec2 uv3;","#endif","#ifdef USE_TANGENT","	attribute vec4 tangent;","#endif","#if defined( USE_COLOR_ALPHA )","	attribute vec4 color;","#elif defined( USE_COLOR )","	attribute vec3 color;","#endif","#ifdef USE_SKINNING","	attribute vec4 skinIndex;","	attribute vec4 skinWeight;","#endif",`
`].filter(_s).join(`
`),f=[Eu(t),"#define SHADER_TYPE "+t.shaderType,"#define SHADER_NAME "+t.shaderName,g,t.useFog&&t.fog?"#define USE_FOG":"",t.useFog&&t.fogExp2?"#define FOG_EXP2":"",t.alphaToCoverage?"#define ALPHA_TO_COVERAGE":"",t.map?"#define USE_MAP":"",t.matcap?"#define USE_MATCAP":"",t.envMap?"#define USE_ENVMAP":"",t.envMap?"#define "+c:"",t.envMap?"#define "+d:"",t.envMap?"#define "+u:"",h?"#define CUBEUV_TEXEL_WIDTH "+h.texelWidth:"",h?"#define CUBEUV_TEXEL_HEIGHT "+h.texelHeight:"",h?"#define CUBEUV_MAX_MIP "+h.maxMip+".0":"",t.lightMap?"#define USE_LIGHTMAP":"",t.aoMap?"#define USE_AOMAP":"",t.bumpMap?"#define USE_BUMPMAP":"",t.normalMap?"#define USE_NORMALMAP":"",t.normalMapObjectSpace?"#define USE_NORMALMAP_OBJECTSPACE":"",t.normalMapTangentSpace?"#define USE_NORMALMAP_TANGENTSPACE":"",t.emissiveMap?"#define USE_EMISSIVEMAP":"",t.anisotropy?"#define USE_ANISOTROPY":"",t.anisotropyMap?"#define USE_ANISOTROPYMAP":"",t.clearcoat?"#define USE_CLEARCOAT":"",t.clearcoatMap?"#define USE_CLEARCOATMAP":"",t.clearcoatRoughnessMap?"#define USE_CLEARCOAT_ROUGHNESSMAP":"",t.clearcoatNormalMap?"#define USE_CLEARCOAT_NORMALMAP":"",t.dispersion?"#define USE_DISPERSION":"",t.iridescence?"#define USE_IRIDESCENCE":"",t.iridescenceMap?"#define USE_IRIDESCENCEMAP":"",t.iridescenceThicknessMap?"#define USE_IRIDESCENCE_THICKNESSMAP":"",t.specularMap?"#define USE_SPECULARMAP":"",t.specularColorMap?"#define USE_SPECULAR_COLORMAP":"",t.specularIntensityMap?"#define USE_SPECULAR_INTENSITYMAP":"",t.roughnessMap?"#define USE_ROUGHNESSMAP":"",t.metalnessMap?"#define USE_METALNESSMAP":"",t.alphaMap?"#define USE_ALPHAMAP":"",t.alphaTest?"#define USE_ALPHATEST":"",t.alphaHash?"#define USE_ALPHAHASH":"",t.sheen?"#define USE_SHEEN":"",t.sheenColorMap?"#define USE_SHEEN_COLORMAP":"",t.sheenRoughnessMap?"#define USE_SHEEN_ROUGHNESSMAP":"",t.transmission?"#define USE_TRANSMISSION":"",t.transmissionMap?"#define USE_TRANSMISSIONMAP":"",t.thicknessMap?"#define USE_THICKNESSMAP":"",t.vertexTangents&&t.flatShading===!1?"#define USE_TANGENT":"",t.vertexColors||t.instancingColor||t.batchingColor?"#define USE_COLOR":"",t.vertexAlphas?"#define USE_COLOR_ALPHA":"",t.vertexUv1s?"#define USE_UV1":"",t.vertexUv2s?"#define USE_UV2":"",t.vertexUv3s?"#define USE_UV3":"",t.pointsUvs?"#define USE_POINTS_UV":"",t.gradientMap?"#define USE_GRADIENTMAP":"",t.flatShading?"#define FLAT_SHADED":"",t.doubleSided?"#define DOUBLE_SIDED":"",t.flipSided?"#define FLIP_SIDED":"",t.shadowMapEnabled?"#define USE_SHADOWMAP":"",t.shadowMapEnabled?"#define "+l:"",t.premultipliedAlpha?"#define PREMULTIPLIED_ALPHA":"",t.numLightProbes>0?"#define USE_LIGHT_PROBES":"",t.decodeVideoTexture?"#define DECODE_VIDEO_TEXTURE":"",t.decodeVideoTextureEmissive?"#define DECODE_VIDEO_TEXTURE_EMISSIVE":"",t.logarithmicDepthBuffer?"#define USE_LOGARITHMIC_DEPTH_BUFFER":"",t.reversedDepthBuffer?"#define USE_REVERSED_DEPTH_BUFFER":"","uniform mat4 viewMatrix;","uniform vec3 cameraPosition;","uniform bool isOrthographic;",t.toneMapping!==$n?"#define TONE_MAPPING":"",t.toneMapping!==$n?Ve.tonemapping_pars_fragment:"",t.toneMapping!==$n?d0("toneMapping",t.toneMapping):"",t.dithering?"#define DITHERING":"",t.opaque?"#define OPAQUE":"",Ve.colorspace_pars_fragment,c0("linearToOutputTexel",t.outputColorSpace),u0(),t.useDepthPacking?"#define DEPTH_PACKING "+t.depthPacking:"",`
`].filter(_s).join(`
`)),a=ac(a),a=wu(a,t),a=Mu(a,t),o=ac(o),o=wu(o,t),o=Mu(o,t),a=Su(a),o=Su(o),t.isRawShaderMaterial!==!0&&(S=`#version 300 es
`,m=[p,"#define attribute in","#define varying out","#define texture2D texture"].join(`
`)+`
`+m,f=["#define varying in",t.glslVersion===Wl?"":"layout(location = 0) out highp vec4 pc_fragColor;",t.glslVersion===Wl?"":"#define gl_FragColor pc_fragColor","#define gl_FragDepthEXT gl_FragDepth","#define texture2D texture","#define textureCube texture","#define texture2DProj textureProj","#define texture2DLodEXT textureLod","#define texture2DProjLodEXT textureProjLod","#define textureCubeLodEXT textureLod","#define texture2DGradEXT textureGrad","#define texture2DProjGradEXT textureProjGrad","#define textureCubeGradEXT textureGrad"].join(`
`)+`
`+f);let M=S+m+a,y=S+f+o,C=yu(r,r.VERTEX_SHADER,M),E=yu(r,r.FRAGMENT_SHADER,y);r.attachShader(x,C),r.attachShader(x,E),t.index0AttributeName!==void 0?r.bindAttribLocation(x,0,t.index0AttributeName):t.morphTargets===!0&&r.bindAttribLocation(x,0,"position"),r.linkProgram(x);function R(T){if(i.debug.checkShaderErrors){let D=r.getProgramInfoLog(x)||"",F=r.getShaderInfoLog(C)||"",B=r.getShaderInfoLog(E)||"",k=D.trim(),W=F.trim(),X=B.trim(),H=!0,Q=!0;if(r.getProgramParameter(x,r.LINK_STATUS)===!1)if(H=!1,typeof i.debug.onShaderError=="function")i.debug.onShaderError(r,x,C,E);else{let ne=bu(r,C,"vertex"),fe=bu(r,E,"fragment");console.error("THREE.WebGLProgram: Shader Error "+r.getError()+" - VALIDATE_STATUS "+r.getProgramParameter(x,r.VALIDATE_STATUS)+`

Material Name: `+T.name+`
Material Type: `+T.type+`

Program Info Log: `+k+`
`+ne+`
`+fe)}else k!==""?console.warn("THREE.WebGLProgram: Program Info Log:",k):(W===""||X==="")&&(Q=!1);Q&&(T.diagnostics={runnable:H,programLog:k,vertexShader:{log:W,prefix:m},fragmentShader:{log:X,prefix:f}})}r.deleteShader(C),r.deleteShader(E),P=new wr(r,x),w=p0(r,x)}let P;this.getUniforms=function(){return P===void 0&&R(this),P};let w;this.getAttributes=function(){return w===void 0&&R(this),w};let v=t.rendererExtensionParallelShaderCompile===!1;return this.isReady=function(){return v===!1&&(v=r.getProgramParameter(x,s0)),v},this.destroy=function(){n.releaseStatesOfProgram(this),r.deleteProgram(x),this.program=void 0},this.type=t.shaderType,this.name=t.shaderName,this.id=a0++,this.cacheKey=e,this.usedTimes=1,this.program=x,this.vertexShader=C,this.fragmentShader=E,this}var T0=0,oc=class{constructor(){this.shaderCache=new Map,this.materialCache=new Map}update(e){let t=e.vertexShader,n=e.fragmentShader,r=this._getShaderStage(t),s=this._getShaderStage(n),a=this._getShaderCacheForMaterial(e);return a.has(r)===!1&&(a.add(r),r.usedTimes++),a.has(s)===!1&&(a.add(s),s.usedTimes++),this}remove(e){let t=this.materialCache.get(e);for(let n of t)n.usedTimes--,n.usedTimes===0&&this.shaderCache.delete(n.code);return this.materialCache.delete(e),this}getVertexShaderID(e){return this._getShaderStage(e.vertexShader).id}getFragmentShaderID(e){return this._getShaderStage(e.fragmentShader).id}dispose(){this.shaderCache.clear(),this.materialCache.clear()}_getShaderCacheForMaterial(e){let t=this.materialCache,n=t.get(e);return n===void 0&&(n=new Set,t.set(e,n)),n}_getShaderStage(e){let t=this.shaderCache,n=t.get(e);return n===void 0&&(n=new lc(e),t.set(e,n)),n}},lc=class{constructor(e){this.id=T0++,this.code=e,this.usedTimes=0}};function A0(i,e,t,n,r,s,a){let o=new Wr,l=new oc,c=new Set,d=[],u=r.logarithmicDepthBuffer,h=r.vertexTextures,p=r.precision,g={MeshDepthMaterial:"depth",MeshDistanceMaterial:"distanceRGBA",MeshNormalMaterial:"normal",MeshBasicMaterial:"basic",MeshLambertMaterial:"lambert",MeshPhongMaterial:"phong",MeshToonMaterial:"toon",MeshStandardMaterial:"physical",MeshPhysicalMaterial:"physical",MeshMatcapMaterial:"matcap",LineBasicMaterial:"basic",LineDashedMaterial:"dashed",PointsMaterial:"points",ShadowMaterial:"shadow",SpriteMaterial:"sprite"};function x(w){return c.add(w),w===0?"uv":`uv${w}`}function m(w,v,T,D,F){let B=D.fog,k=F.geometry,W=w.isMeshStandardMaterial?D.environment:null,X=(w.isMeshStandardMaterial?t:e).get(w.envMap||W),H=X&&X.mapping===hs?X.image.height:null,Q=g[w.type];w.precision!==null&&(p=r.getMaxPrecision(w.precision),p!==w.precision&&console.warn("THREE.WebGLProgram.getParameters:",w.precision,"not supported, using",p,"instead."));let ne=k.morphAttributes.position||k.morphAttributes.normal||k.morphAttributes.color,fe=ne!==void 0?ne.length:0,De=0;k.morphAttributes.position!==void 0&&(De=1),k.morphAttributes.normal!==void 0&&(De=2),k.morphAttributes.color!==void 0&&(De=3);let Xe,Ze,Fe,Y;if(Q){let Ye=Nn[Q];Xe=Ye.vertexShader,Ze=Ye.fragmentShader}else Xe=w.vertexShader,Ze=w.fragmentShader,l.update(w),Fe=l.getVertexShaderID(w),Y=l.getFragmentShaderID(w);let J=i.getRenderTarget(),pe=i.state.buffers.depth.getReversed(),Ce=F.isInstancedMesh===!0,ge=F.isBatchedMesh===!0,ze=!!w.map,xt=!!w.matcap,I=!!X,ot=!!w.aoMap,Ue=!!w.lightMap,Ie=!!w.bumpMap,ye=!!w.normalMap,lt=!!w.displacementMap,ve=!!w.emissiveMap,ke=!!w.metalnessMap,At=!!w.roughnessMap,vt=w.anisotropy>0,A=w.clearcoat>0,_=w.dispersion>0,z=w.iridescence>0,q=w.sheen>0,K=w.transmission>0,$=vt&&!!w.anisotropyMap,Se=A&&!!w.clearcoatMap,se=A&&!!w.clearcoatNormalMap,be=A&&!!w.clearcoatRoughnessMap,we=z&&!!w.iridescenceMap,ie=z&&!!w.iridescenceThicknessMap,de=q&&!!w.sheenColorMap,Re=q&&!!w.sheenRoughnessMap,Me=!!w.specularMap,le=!!w.specularColorMap,Be=!!w.specularIntensityMap,L=K&&!!w.transmissionMap,re=K&&!!w.thicknessMap,ae=!!w.gradientMap,me=!!w.alphaMap,ee=w.alphaTest>0,Z=!!w.alphaHash,_e=!!w.extensions,Le=$n;w.toneMapped&&(J===null||J.isXRRenderTarget===!0)&&(Le=i.toneMapping);let nt={shaderID:Q,shaderType:w.type,shaderName:w.name,vertexShader:Xe,fragmentShader:Ze,defines:w.defines,customVertexShaderID:Fe,customFragmentShaderID:Y,isRawShaderMaterial:w.isRawShaderMaterial===!0,glslVersion:w.glslVersion,precision:p,batching:ge,batchingColor:ge&&F._colorsTexture!==null,instancing:Ce,instancingColor:Ce&&F.instanceColor!==null,instancingMorph:Ce&&F.morphTexture!==null,supportsVertexTextures:h,outputColorSpace:J===null?i.outputColorSpace:J.isXRRenderTarget===!0?J.texture.colorSpace:Si,alphaToCoverage:!!w.alphaToCoverage,map:ze,matcap:xt,envMap:I,envMapMode:I&&X.mapping,envMapCubeUVHeight:H,aoMap:ot,lightMap:Ue,bumpMap:Ie,normalMap:ye,displacementMap:h&&lt,emissiveMap:ve,normalMapObjectSpace:ye&&w.normalMapType===$d,normalMapTangentSpace:ye&&w.normalMapType===Vl,metalnessMap:ke,roughnessMap:At,anisotropy:vt,anisotropyMap:$,clearcoat:A,clearcoatMap:Se,clearcoatNormalMap:se,clearcoatRoughnessMap:be,dispersion:_,iridescence:z,iridescenceMap:we,iridescenceThicknessMap:ie,sheen:q,sheenColorMap:de,sheenRoughnessMap:Re,specularMap:Me,specularColorMap:le,specularIntensityMap:Be,transmission:K,transmissionMap:L,thicknessMap:re,gradientMap:ae,opaque:w.transparent===!1&&w.blending===wi&&w.alphaToCoverage===!1,alphaMap:me,alphaTest:ee,alphaHash:Z,combine:w.combine,mapUv:ze&&x(w.map.channel),aoMapUv:ot&&x(w.aoMap.channel),lightMapUv:Ue&&x(w.lightMap.channel),bumpMapUv:Ie&&x(w.bumpMap.channel),normalMapUv:ye&&x(w.normalMap.channel),displacementMapUv:lt&&x(w.displacementMap.channel),emissiveMapUv:ve&&x(w.emissiveMap.channel),metalnessMapUv:ke&&x(w.metalnessMap.channel),roughnessMapUv:At&&x(w.roughnessMap.channel),anisotropyMapUv:$&&x(w.anisotropyMap.channel),clearcoatMapUv:Se&&x(w.clearcoatMap.channel),clearcoatNormalMapUv:se&&x(w.clearcoatNormalMap.channel),clearcoatRoughnessMapUv:be&&x(w.clearcoatRoughnessMap.channel),iridescenceMapUv:we&&x(w.iridescenceMap.channel),iridescenceThicknessMapUv:ie&&x(w.iridescenceThicknessMap.channel),sheenColorMapUv:de&&x(w.sheenColorMap.channel),sheenRoughnessMapUv:Re&&x(w.sheenRoughnessMap.channel),specularMapUv:Me&&x(w.specularMap.channel),specularColorMapUv:le&&x(w.specularColorMap.channel),specularIntensityMapUv:Be&&x(w.specularIntensityMap.channel),transmissionMapUv:L&&x(w.transmissionMap.channel),thicknessMapUv:re&&x(w.thicknessMap.channel),alphaMapUv:me&&x(w.alphaMap.channel),vertexTangents:!!k.attributes.tangent&&(ye||vt),vertexColors:w.vertexColors,vertexAlphas:w.vertexColors===!0&&!!k.attributes.color&&k.attributes.color.itemSize===4,pointsUvs:F.isPoints===!0&&!!k.attributes.uv&&(ze||me),fog:!!B,useFog:w.fog===!0,fogExp2:!!B&&B.isFogExp2,flatShading:w.flatShading===!0&&w.wireframe===!1,sizeAttenuation:w.sizeAttenuation===!0,logarithmicDepthBuffer:u,reversedDepthBuffer:pe,skinning:F.isSkinnedMesh===!0,morphTargets:k.morphAttributes.position!==void 0,morphNormals:k.morphAttributes.normal!==void 0,morphColors:k.morphAttributes.color!==void 0,morphTargetsCount:fe,morphTextureStride:De,numDirLights:v.directional.length,numPointLights:v.point.length,numSpotLights:v.spot.length,numSpotLightMaps:v.spotLightMap.length,numRectAreaLights:v.rectArea.length,numHemiLights:v.hemi.length,numDirLightShadows:v.directionalShadowMap.length,numPointLightShadows:v.pointShadowMap.length,numSpotLightShadows:v.spotShadowMap.length,numSpotLightShadowsWithMaps:v.numSpotLightShadowsWithMaps,numLightProbes:v.numLightProbes,numClippingPlanes:a.numPlanes,numClipIntersection:a.numIntersection,dithering:w.dithering,shadowMapEnabled:i.shadowMap.enabled&&T.length>0,shadowMapType:i.shadowMap.type,toneMapping:Le,decodeVideoTexture:ze&&w.map.isVideoTexture===!0&&$e.getTransfer(w.map.colorSpace)===Ke,decodeVideoTextureEmissive:ve&&w.emissiveMap.isVideoTexture===!0&&$e.getTransfer(w.emissiveMap.colorSpace)===Ke,premultipliedAlpha:w.premultipliedAlpha,doubleSided:w.side===dn,flipSided:w.side===zt,useDepthPacking:w.depthPacking>=0,depthPacking:w.depthPacking||0,index0AttributeName:w.index0AttributeName,extensionClipCullDistance:_e&&w.extensions.clipCullDistance===!0&&n.has("WEBGL_clip_cull_distance"),extensionMultiDraw:(_e&&w.extensions.multiDraw===!0||ge)&&n.has("WEBGL_multi_draw"),rendererExtensionParallelShaderCompile:n.has("KHR_parallel_shader_compile"),customProgramCacheKey:w.customProgramCacheKey()};return nt.vertexUv1s=c.has(1),nt.vertexUv2s=c.has(2),nt.vertexUv3s=c.has(3),c.clear(),nt}function f(w){let v=[];if(w.shaderID?v.push(w.shaderID):(v.push(w.customVertexShaderID),v.push(w.customFragmentShaderID)),w.defines!==void 0)for(let T in w.defines)v.push(T),v.push(w.defines[T]);return w.isRawShaderMaterial===!1&&(S(v,w),M(v,w),v.push(i.outputColorSpace)),v.push(w.customProgramCacheKey),v.join()}function S(w,v){w.push(v.precision),w.push(v.outputColorSpace),w.push(v.envMapMode),w.push(v.envMapCubeUVHeight),w.push(v.mapUv),w.push(v.alphaMapUv),w.push(v.lightMapUv),w.push(v.aoMapUv),w.push(v.bumpMapUv),w.push(v.normalMapUv),w.push(v.displacementMapUv),w.push(v.emissiveMapUv),w.push(v.metalnessMapUv),w.push(v.roughnessMapUv),w.push(v.anisotropyMapUv),w.push(v.clearcoatMapUv),w.push(v.clearcoatNormalMapUv),w.push(v.clearcoatRoughnessMapUv),w.push(v.iridescenceMapUv),w.push(v.iridescenceThicknessMapUv),w.push(v.sheenColorMapUv),w.push(v.sheenRoughnessMapUv),w.push(v.specularMapUv),w.push(v.specularColorMapUv),w.push(v.specularIntensityMapUv),w.push(v.transmissionMapUv),w.push(v.thicknessMapUv),w.push(v.combine),w.push(v.fogExp2),w.push(v.sizeAttenuation),w.push(v.morphTargetsCount),w.push(v.morphAttributeCount),w.push(v.numDirLights),w.push(v.numPointLights),w.push(v.numSpotLights),w.push(v.numSpotLightMaps),w.push(v.numHemiLights),w.push(v.numRectAreaLights),w.push(v.numDirLightShadows),w.push(v.numPointLightShadows),w.push(v.numSpotLightShadows),w.push(v.numSpotLightShadowsWithMaps),w.push(v.numLightProbes),w.push(v.shadowMapType),w.push(v.toneMapping),w.push(v.numClippingPlanes),w.push(v.numClipIntersection),w.push(v.depthPacking)}function M(w,v){o.disableAll(),v.supportsVertexTextures&&o.enable(0),v.instancing&&o.enable(1),v.instancingColor&&o.enable(2),v.instancingMorph&&o.enable(3),v.matcap&&o.enable(4),v.envMap&&o.enable(5),v.normalMapObjectSpace&&o.enable(6),v.normalMapTangentSpace&&o.enable(7),v.clearcoat&&o.enable(8),v.iridescence&&o.enable(9),v.alphaTest&&o.enable(10),v.vertexColors&&o.enable(11),v.vertexAlphas&&o.enable(12),v.vertexUv1s&&o.enable(13),v.vertexUv2s&&o.enable(14),v.vertexUv3s&&o.enable(15),v.vertexTangents&&o.enable(16),v.anisotropy&&o.enable(17),v.alphaHash&&o.enable(18),v.batching&&o.enable(19),v.dispersion&&o.enable(20),v.batchingColor&&o.enable(21),v.gradientMap&&o.enable(22),w.push(o.mask),o.disableAll(),v.fog&&o.enable(0),v.useFog&&o.enable(1),v.flatShading&&o.enable(2),v.logarithmicDepthBuffer&&o.enable(3),v.reversedDepthBuffer&&o.enable(4),v.skinning&&o.enable(5),v.morphTargets&&o.enable(6),v.morphNormals&&o.enable(7),v.morphColors&&o.enable(8),v.premultipliedAlpha&&o.enable(9),v.shadowMapEnabled&&o.enable(10),v.doubleSided&&o.enable(11),v.flipSided&&o.enable(12),v.useDepthPacking&&o.enable(13),v.dithering&&o.enable(14),v.transmission&&o.enable(15),v.sheen&&o.enable(16),v.opaque&&o.enable(17),v.pointsUvs&&o.enable(18),v.decodeVideoTexture&&o.enable(19),v.decodeVideoTextureEmissive&&o.enable(20),v.alphaToCoverage&&o.enable(21),w.push(o.mask)}function y(w){let v=g[w.type],T;if(v){let D=Nn[v];T=iu.clone(D.uniforms)}else T=w.uniforms;return T}function C(w,v){let T;for(let D=0,F=d.length;D<F;D++){let B=d[D];if(B.cacheKey===v){T=B,++T.usedTimes;break}}return T===void 0&&(T=new E0(i,v,w,s),d.push(T)),T}function E(w){if(--w.usedTimes===0){let v=d.indexOf(w);d[v]=d[d.length-1],d.pop(),w.destroy()}}function R(w){l.remove(w)}function P(){l.dispose()}return{getParameters:m,getProgramCacheKey:f,getUniforms:y,acquireProgram:C,releaseProgram:E,releaseShaderCache:R,programs:d,dispose:P}}function C0(){let i=new WeakMap;function e(a){return i.has(a)}function t(a){let o=i.get(a);return o===void 0&&(o={},i.set(a,o)),o}function n(a){i.delete(a)}function r(a,o,l){i.get(a)[o]=l}function s(){i=new WeakMap}return{has:e,get:t,remove:n,update:r,dispose:s}}function R0(i,e){return i.groupOrder!==e.groupOrder?i.groupOrder-e.groupOrder:i.renderOrder!==e.renderOrder?i.renderOrder-e.renderOrder:i.material.id!==e.material.id?i.material.id-e.material.id:i.z!==e.z?i.z-e.z:i.id-e.id}function Tu(i,e){return i.groupOrder!==e.groupOrder?i.groupOrder-e.groupOrder:i.renderOrder!==e.renderOrder?i.renderOrder-e.renderOrder:i.z!==e.z?e.z-i.z:i.id-e.id}function Au(){let i=[],e=0,t=[],n=[],r=[];function s(){e=0,t.length=0,n.length=0,r.length=0}function a(u,h,p,g,x,m){let f=i[e];return f===void 0?(f={id:u.id,object:u,geometry:h,material:p,groupOrder:g,renderOrder:u.renderOrder,z:x,group:m},i[e]=f):(f.id=u.id,f.object=u,f.geometry=h,f.material=p,f.groupOrder=g,f.renderOrder=u.renderOrder,f.z=x,f.group=m),e++,f}function o(u,h,p,g,x,m){let f=a(u,h,p,g,x,m);p.transmission>0?n.push(f):p.transparent===!0?r.push(f):t.push(f)}function l(u,h,p,g,x,m){let f=a(u,h,p,g,x,m);p.transmission>0?n.unshift(f):p.transparent===!0?r.unshift(f):t.unshift(f)}function c(u,h){t.length>1&&t.sort(u||R0),n.length>1&&n.sort(h||Tu),r.length>1&&r.sort(h||Tu)}function d(){for(let u=e,h=i.length;u<h;u++){let p=i[u];if(p.id===null)break;p.id=null,p.object=null,p.geometry=null,p.material=null,p.group=null}}return{opaque:t,transmissive:n,transparent:r,init:s,push:o,unshift:l,finish:d,sort:c}}function I0(){let i=new WeakMap;function e(n,r){let s=i.get(n),a;return s===void 0?(a=new Au,i.set(n,[a])):r>=s.length?(a=new Au,s.push(a)):a=s[r],a}function t(){i=new WeakMap}return{get:e,dispose:t}}function P0(){let i={};return{get:function(e){if(i[e.id]!==void 0)return i[e.id];let t;switch(e.type){case"DirectionalLight":t={direction:new N,color:new Ne};break;case"SpotLight":t={position:new N,direction:new N,color:new Ne,distance:0,coneCos:0,penumbraCos:0,decay:0};break;case"PointLight":t={position:new N,color:new Ne,distance:0,decay:0};break;case"HemisphereLight":t={direction:new N,skyColor:new Ne,groundColor:new Ne};break;case"RectAreaLight":t={color:new Ne,position:new N,halfWidth:new N,halfHeight:new N};break}return i[e.id]=t,t}}}function N0(){let i={};return{get:function(e){if(i[e.id]!==void 0)return i[e.id];let t;switch(e.type){case"DirectionalLight":t={shadowIntensity:1,shadowBias:0,shadowNormalBias:0,shadowRadius:1,shadowMapSize:new He};break;case"SpotLight":t={shadowIntensity:1,shadowBias:0,shadowNormalBias:0,shadowRadius:1,shadowMapSize:new He};break;case"PointLight":t={shadowIntensity:1,shadowBias:0,shadowNormalBias:0,shadowRadius:1,shadowMapSize:new He,shadowCameraNear:1,shadowCameraFar:1e3};break}return i[e.id]=t,t}}}var D0=0;function L0(i,e){return(e.castShadow?2:0)-(i.castShadow?2:0)+(e.map?1:0)-(i.map?1:0)}function F0(i){let e=new P0,t=N0(),n={version:0,hash:{directionalLength:-1,pointLength:-1,spotLength:-1,rectAreaLength:-1,hemiLength:-1,numDirectionalShadows:-1,numPointShadows:-1,numSpotShadows:-1,numSpotMaps:-1,numLightProbes:-1},ambient:[0,0,0],probe:[],directional:[],directionalShadow:[],directionalShadowMap:[],directionalShadowMatrix:[],spot:[],spotLightMap:[],spotShadow:[],spotShadowMap:[],spotLightMatrix:[],rectArea:[],rectAreaLTC1:null,rectAreaLTC2:null,point:[],pointShadow:[],pointShadowMap:[],pointShadowMatrix:[],hemi:[],numSpotLightShadowsWithMaps:0,numLightProbes:0};for(let c=0;c<9;c++)n.probe.push(new N);let r=new N,s=new ct,a=new ct;function o(c){let d=0,u=0,h=0;for(let w=0;w<9;w++)n.probe[w].set(0,0,0);let p=0,g=0,x=0,m=0,f=0,S=0,M=0,y=0,C=0,E=0,R=0;c.sort(L0);for(let w=0,v=c.length;w<v;w++){let T=c[w],D=T.color,F=T.intensity,B=T.distance,k=T.shadow&&T.shadow.map?T.shadow.map.texture:null;if(T.isAmbientLight)d+=D.r*F,u+=D.g*F,h+=D.b*F;else if(T.isLightProbe){for(let W=0;W<9;W++)n.probe[W].addScaledVector(T.sh.coefficients[W],F);R++}else if(T.isDirectionalLight){let W=e.get(T);if(W.color.copy(T.color).multiplyScalar(T.intensity),T.castShadow){let X=T.shadow,H=t.get(T);H.shadowIntensity=X.intensity,H.shadowBias=X.bias,H.shadowNormalBias=X.normalBias,H.shadowRadius=X.radius,H.shadowMapSize=X.mapSize,n.directionalShadow[p]=H,n.directionalShadowMap[p]=k,n.directionalShadowMatrix[p]=T.shadow.matrix,S++}n.directional[p]=W,p++}else if(T.isSpotLight){let W=e.get(T);W.position.setFromMatrixPosition(T.matrixWorld),W.color.copy(D).multiplyScalar(F),W.distance=B,W.coneCos=Math.cos(T.angle),W.penumbraCos=Math.cos(T.angle*(1-T.penumbra)),W.decay=T.decay,n.spot[x]=W;let X=T.shadow;if(T.map&&(n.spotLightMap[C]=T.map,C++,X.updateMatrices(T),T.castShadow&&E++),n.spotLightMatrix[x]=X.matrix,T.castShadow){let H=t.get(T);H.shadowIntensity=X.intensity,H.shadowBias=X.bias,H.shadowNormalBias=X.normalBias,H.shadowRadius=X.radius,H.shadowMapSize=X.mapSize,n.spotShadow[x]=H,n.spotShadowMap[x]=k,y++}x++}else if(T.isRectAreaLight){let W=e.get(T);W.color.copy(D).multiplyScalar(F),W.halfWidth.set(T.width*.5,0,0),W.halfHeight.set(0,T.height*.5,0),n.rectArea[m]=W,m++}else if(T.isPointLight){let W=e.get(T);if(W.color.copy(T.color).multiplyScalar(T.intensity),W.distance=T.distance,W.decay=T.decay,T.castShadow){let X=T.shadow,H=t.get(T);H.shadowIntensity=X.intensity,H.shadowBias=X.bias,H.shadowNormalBias=X.normalBias,H.shadowRadius=X.radius,H.shadowMapSize=X.mapSize,H.shadowCameraNear=X.camera.near,H.shadowCameraFar=X.camera.far,n.pointShadow[g]=H,n.pointShadowMap[g]=k,n.pointShadowMatrix[g]=T.shadow.matrix,M++}n.point[g]=W,g++}else if(T.isHemisphereLight){let W=e.get(T);W.skyColor.copy(T.color).multiplyScalar(F),W.groundColor.copy(T.groundColor).multiplyScalar(F),n.hemi[f]=W,f++}}m>0&&(i.has("OES_texture_float_linear")===!0?(n.rectAreaLTC1=oe.LTC_FLOAT_1,n.rectAreaLTC2=oe.LTC_FLOAT_2):(n.rectAreaLTC1=oe.LTC_HALF_1,n.rectAreaLTC2=oe.LTC_HALF_2)),n.ambient[0]=d,n.ambient[1]=u,n.ambient[2]=h;let P=n.hash;(P.directionalLength!==p||P.pointLength!==g||P.spotLength!==x||P.rectAreaLength!==m||P.hemiLength!==f||P.numDirectionalShadows!==S||P.numPointShadows!==M||P.numSpotShadows!==y||P.numSpotMaps!==C||P.numLightProbes!==R)&&(n.directional.length=p,n.spot.length=x,n.rectArea.length=m,n.point.length=g,n.hemi.length=f,n.directionalShadow.length=S,n.directionalShadowMap.length=S,n.pointShadow.length=M,n.pointShadowMap.length=M,n.spotShadow.length=y,n.spotShadowMap.length=y,n.directionalShadowMatrix.length=S,n.pointShadowMatrix.length=M,n.spotLightMatrix.length=y+C-E,n.spotLightMap.length=C,n.numSpotLightShadowsWithMaps=E,n.numLightProbes=R,P.directionalLength=p,P.pointLength=g,P.spotLength=x,P.rectAreaLength=m,P.hemiLength=f,P.numDirectionalShadows=S,P.numPointShadows=M,P.numSpotShadows=y,P.numSpotMaps=C,P.numLightProbes=R,n.version=D0++)}function l(c,d){let u=0,h=0,p=0,g=0,x=0,m=d.matrixWorldInverse;for(let f=0,S=c.length;f<S;f++){let M=c[f];if(M.isDirectionalLight){let y=n.directional[u];y.direction.setFromMatrixPosition(M.matrixWorld),r.setFromMatrixPosition(M.target.matrixWorld),y.direction.sub(r),y.direction.transformDirection(m),u++}else if(M.isSpotLight){let y=n.spot[p];y.position.setFromMatrixPosition(M.matrixWorld),y.position.applyMatrix4(m),y.direction.setFromMatrixPosition(M.matrixWorld),r.setFromMatrixPosition(M.target.matrixWorld),y.direction.sub(r),y.direction.transformDirection(m),p++}else if(M.isRectAreaLight){let y=n.rectArea[g];y.position.setFromMatrixPosition(M.matrixWorld),y.position.applyMatrix4(m),a.identity(),s.copy(M.matrixWorld),s.premultiply(m),a.extractRotation(s),y.halfWidth.set(M.width*.5,0,0),y.halfHeight.set(0,M.height*.5,0),y.halfWidth.applyMatrix4(a),y.halfHeight.applyMatrix4(a),g++}else if(M.isPointLight){let y=n.point[h];y.position.setFromMatrixPosition(M.matrixWorld),y.position.applyMatrix4(m),h++}else if(M.isHemisphereLight){let y=n.hemi[x];y.direction.setFromMatrixPosition(M.matrixWorld),y.direction.transformDirection(m),x++}}}return{setup:o,setupView:l,state:n}}function Cu(i){let e=new F0(i),t=[],n=[];function r(d){c.camera=d,t.length=0,n.length=0}function s(d){t.push(d)}function a(d){n.push(d)}function o(){e.setup(t)}function l(d){e.setupView(t,d)}let c={lightsArray:t,shadowsArray:n,camera:null,lights:e,transmissionRenderTarget:{}};return{init:r,state:c,setupLights:o,setupLightsView:l,pushLight:s,pushShadow:a}}function U0(i){let e=new WeakMap;function t(r,s=0){let a=e.get(r),o;return a===void 0?(o=new Cu(i),e.set(r,[o])):s>=a.length?(o=new Cu(i),a.push(o)):o=a[s],o}function n(){e=new WeakMap}return{get:t,dispose:n}}var O0=`void main() {
	gl_Position = vec4( position, 1.0 );
}`,B0=`uniform sampler2D shadow_pass;
uniform vec2 resolution;
uniform float radius;
#include <packing>
void main() {
	const float samples = float( VSM_SAMPLES );
	float mean = 0.0;
	float squared_mean = 0.0;
	float uvStride = samples <= 1.0 ? 0.0 : 2.0 / ( samples - 1.0 );
	float uvStart = samples <= 1.0 ? 0.0 : - 1.0;
	for ( float i = 0.0; i < samples; i ++ ) {
		float uvOffset = uvStart + i * uvStride;
		#ifdef HORIZONTAL_PASS
			vec2 distribution = unpackRGBATo2Half( texture2D( shadow_pass, ( gl_FragCoord.xy + vec2( uvOffset, 0.0 ) * radius ) / resolution ) );
			mean += distribution.x;
			squared_mean += distribution.y * distribution.y + distribution.x * distribution.x;
		#else
			float depth = unpackRGBAToDepth( texture2D( shadow_pass, ( gl_FragCoord.xy + vec2( 0.0, uvOffset ) * radius ) / resolution ) );
			mean += depth;
			squared_mean += depth * depth;
		#endif
	}
	mean = mean / samples;
	squared_mean = squared_mean / samples;
	float std_dev = sqrt( squared_mean - mean * mean );
	gl_FragColor = pack2HalfToRGBA( vec2( mean, std_dev ) );
}`;function z0(i,e,t){let n=new pr,r=new He,s=new He,a=new pt,o=new ba({depthPacking:Xd}),l=new wa,c={},d=t.maxTextureSize,u={[Vn]:zt,[zt]:Vn,[dn]:dn},h=new tn({defines:{VSM_SAMPLES:8},uniforms:{shadow_pass:{value:null},resolution:{value:new He},radius:{value:4}},vertexShader:O0,fragmentShader:B0}),p=h.clone();p.defines.HORIZONTAL_PASS=1;let g=new dt;g.setAttribute("position",new Gt(new Float32Array([-1,-1,.5,3,-1,.5,-1,3,.5]),3));let x=new st(g,h),m=this;this.enabled=!1,this.autoUpdate=!0,this.needsUpdate=!1,this.type=Cl;let f=this.type;this.render=function(E,R,P){if(m.enabled===!1||m.autoUpdate===!1&&m.needsUpdate===!1||E.length===0)return;let w=i.getRenderTarget(),v=i.getActiveCubeFace(),T=i.getActiveMipmapLevel(),D=i.state;D.setBlending(Xn),D.buffers.depth.getReversed()===!0?D.buffers.color.setClear(0,0,0,0):D.buffers.color.setClear(1,1,1,1),D.buffers.depth.setTest(!0),D.setScissorTest(!1);let F=f!==In&&this.type===In,B=f===In&&this.type!==In;for(let k=0,W=E.length;k<W;k++){let X=E[k],H=X.shadow;if(H===void 0){console.warn("THREE.WebGLShadowMap:",X,"has no shadow.");continue}if(H.autoUpdate===!1&&H.needsUpdate===!1)continue;r.copy(H.mapSize);let Q=H.getFrameExtents();if(r.multiply(Q),s.copy(H.mapSize),(r.x>d||r.y>d)&&(r.x>d&&(s.x=Math.floor(d/Q.x),r.x=s.x*Q.x,H.mapSize.x=s.x),r.y>d&&(s.y=Math.floor(d/Q.y),r.y=s.y*Q.y,H.mapSize.y=s.y)),H.map===null||F===!0||B===!0){let fe=this.type!==In?{minFilter:cn,magFilter:cn}:{};H.map!==null&&H.map.dispose(),H.map=new Cn(r.x,r.y,fe),H.map.texture.name=X.name+".shadowMap",H.camera.updateProjectionMatrix()}i.setRenderTarget(H.map),i.clear();let ne=H.getViewportCount();for(let fe=0;fe<ne;fe++){let De=H.getViewport(fe);a.set(s.x*De.x,s.y*De.y,s.x*De.z,s.y*De.w),D.viewport(a),H.updateMatrices(X,fe),n=H.getFrustum(),y(R,P,H.camera,X,this.type)}H.isPointLightShadow!==!0&&this.type===In&&S(H,P),H.needsUpdate=!1}f=this.type,m.needsUpdate=!1,i.setRenderTarget(w,v,T)};function S(E,R){let P=e.update(x);h.defines.VSM_SAMPLES!==E.blurSamples&&(h.defines.VSM_SAMPLES=E.blurSamples,p.defines.VSM_SAMPLES=E.blurSamples,h.needsUpdate=!0,p.needsUpdate=!0),E.mapPass===null&&(E.mapPass=new Cn(r.x,r.y)),h.uniforms.shadow_pass.value=E.map.texture,h.uniforms.resolution.value=E.mapSize,h.uniforms.radius.value=E.radius,i.setRenderTarget(E.mapPass),i.clear(),i.renderBufferDirect(R,null,P,h,x,null),p.uniforms.shadow_pass.value=E.mapPass.texture,p.uniforms.resolution.value=E.mapSize,p.uniforms.radius.value=E.radius,i.setRenderTarget(E.map),i.clear(),i.renderBufferDirect(R,null,P,p,x,null)}function M(E,R,P,w){let v=null,T=P.isPointLight===!0?E.customDistanceMaterial:E.customDepthMaterial;if(T!==void 0)v=T;else if(v=P.isPointLight===!0?l:o,i.localClippingEnabled&&R.clipShadows===!0&&Array.isArray(R.clippingPlanes)&&R.clippingPlanes.length!==0||R.displacementMap&&R.displacementScale!==0||R.alphaMap&&R.alphaTest>0||R.map&&R.alphaTest>0||R.alphaToCoverage===!0){let D=v.uuid,F=R.uuid,B=c[D];B===void 0&&(B={},c[D]=B);let k=B[F];k===void 0&&(k=v.clone(),B[F]=k,R.addEventListener("dispose",C)),v=k}if(v.visible=R.visible,v.wireframe=R.wireframe,w===In?v.side=R.shadowSide!==null?R.shadowSide:R.side:v.side=R.shadowSide!==null?R.shadowSide:u[R.side],v.alphaMap=R.alphaMap,v.alphaTest=R.alphaToCoverage===!0?.5:R.alphaTest,v.map=R.map,v.clipShadows=R.clipShadows,v.clippingPlanes=R.clippingPlanes,v.clipIntersection=R.clipIntersection,v.displacementMap=R.displacementMap,v.displacementScale=R.displacementScale,v.displacementBias=R.displacementBias,v.wireframeLinewidth=R.wireframeLinewidth,v.linewidth=R.linewidth,P.isPointLight===!0&&v.isMeshDistanceMaterial===!0){let D=i.properties.get(v);D.light=P}return v}function y(E,R,P,w,v){if(E.visible===!1)return;if(E.layers.test(R.layers)&&(E.isMesh||E.isLine||E.isPoints)&&(E.castShadow||E.receiveShadow&&v===In)&&(!E.frustumCulled||n.intersectsObject(E))){E.modelViewMatrix.multiplyMatrices(P.matrixWorldInverse,E.matrixWorld);let F=e.update(E),B=E.material;if(Array.isArray(B)){let k=F.groups;for(let W=0,X=k.length;W<X;W++){let H=k[W],Q=B[H.materialIndex];if(Q&&Q.visible){let ne=M(E,Q,w,v);E.onBeforeShadow(i,E,R,P,F,ne,H),i.renderBufferDirect(P,null,F,ne,E,H),E.onAfterShadow(i,E,R,P,F,ne,H)}}}else if(B.visible){let k=M(E,B,w,v);E.onBeforeShadow(i,E,R,P,F,k,null),i.renderBufferDirect(P,null,F,k,E,null),E.onAfterShadow(i,E,R,P,F,k,null)}}let D=E.children;for(let F=0,B=D.length;F<B;F++)y(D[F],R,P,w,v)}function C(E){E.target.removeEventListener("dispose",C);for(let P in c){let w=c[P],v=E.target.uuid;v in w&&(w[v].dispose(),delete w[v])}}}var k0={[Da]:La,[Fa]:Ba,[Ua]:za,[Mi]:Oa,[La]:Da,[Ba]:Fa,[za]:Ua,[Oa]:Mi};function H0(i,e){function t(){let L=!1,re=new pt,ae=null,me=new pt(0,0,0,0);return{setMask:function(ee){ae!==ee&&!L&&(i.colorMask(ee,ee,ee,ee),ae=ee)},setLocked:function(ee){L=ee},setClear:function(ee,Z,_e,Le,nt){nt===!0&&(ee*=Le,Z*=Le,_e*=Le),re.set(ee,Z,_e,Le),me.equals(re)===!1&&(i.clearColor(ee,Z,_e,Le),me.copy(re))},reset:function(){L=!1,ae=null,me.set(-1,0,0,0)}}}function n(){let L=!1,re=!1,ae=null,me=null,ee=null;return{setReversed:function(Z){if(re!==Z){let _e=e.get("EXT_clip_control");Z?_e.clipControlEXT(_e.LOWER_LEFT_EXT,_e.ZERO_TO_ONE_EXT):_e.clipControlEXT(_e.LOWER_LEFT_EXT,_e.NEGATIVE_ONE_TO_ONE_EXT),re=Z;let Le=ee;ee=null,this.setClear(Le)}},getReversed:function(){return re},setTest:function(Z){Z?J(i.DEPTH_TEST):pe(i.DEPTH_TEST)},setMask:function(Z){ae!==Z&&!L&&(i.depthMask(Z),ae=Z)},setFunc:function(Z){if(re&&(Z=k0[Z]),me!==Z){switch(Z){case Da:i.depthFunc(i.NEVER);break;case La:i.depthFunc(i.ALWAYS);break;case Fa:i.depthFunc(i.LESS);break;case Mi:i.depthFunc(i.LEQUAL);break;case Ua:i.depthFunc(i.EQUAL);break;case Oa:i.depthFunc(i.GEQUAL);break;case Ba:i.depthFunc(i.GREATER);break;case za:i.depthFunc(i.NOTEQUAL);break;default:i.depthFunc(i.LEQUAL)}me=Z}},setLocked:function(Z){L=Z},setClear:function(Z){ee!==Z&&(re&&(Z=1-Z),i.clearDepth(Z),ee=Z)},reset:function(){L=!1,ae=null,me=null,ee=null,re=!1}}}function r(){let L=!1,re=null,ae=null,me=null,ee=null,Z=null,_e=null,Le=null,nt=null;return{setTest:function(Ye){L||(Ye?J(i.STENCIL_TEST):pe(i.STENCIL_TEST))},setMask:function(Ye){re!==Ye&&!L&&(i.stencilMask(Ye),re=Ye)},setFunc:function(Ye,Ln,En){(ae!==Ye||me!==Ln||ee!==En)&&(i.stencilFunc(Ye,Ln,En),ae=Ye,me=Ln,ee=En)},setOp:function(Ye,Ln,En){(Z!==Ye||_e!==Ln||Le!==En)&&(i.stencilOp(Ye,Ln,En),Z=Ye,_e=Ln,Le=En)},setLocked:function(Ye){L=Ye},setClear:function(Ye){nt!==Ye&&(i.clearStencil(Ye),nt=Ye)},reset:function(){L=!1,re=null,ae=null,me=null,ee=null,Z=null,_e=null,Le=null,nt=null}}}let s=new t,a=new n,o=new r,l=new WeakMap,c=new WeakMap,d={},u={},h=new WeakMap,p=[],g=null,x=!1,m=null,f=null,S=null,M=null,y=null,C=null,E=null,R=new Ne(0,0,0),P=0,w=!1,v=null,T=null,D=null,F=null,B=null,k=i.getParameter(i.MAX_COMBINED_TEXTURE_IMAGE_UNITS),W=!1,X=0,H=i.getParameter(i.VERSION);H.indexOf("WebGL")!==-1?(X=parseFloat(/^WebGL (\d)/.exec(H)[1]),W=X>=1):H.indexOf("OpenGL ES")!==-1&&(X=parseFloat(/^OpenGL ES (\d)/.exec(H)[1]),W=X>=2);let Q=null,ne={},fe=i.getParameter(i.SCISSOR_BOX),De=i.getParameter(i.VIEWPORT),Xe=new pt().fromArray(fe),Ze=new pt().fromArray(De);function Fe(L,re,ae,me){let ee=new Uint8Array(4),Z=i.createTexture();i.bindTexture(L,Z),i.texParameteri(L,i.TEXTURE_MIN_FILTER,i.NEAREST),i.texParameteri(L,i.TEXTURE_MAG_FILTER,i.NEAREST);for(let _e=0;_e<ae;_e++)L===i.TEXTURE_3D||L===i.TEXTURE_2D_ARRAY?i.texImage3D(re,0,i.RGBA,1,1,me,0,i.RGBA,i.UNSIGNED_BYTE,ee):i.texImage2D(re+_e,0,i.RGBA,1,1,0,i.RGBA,i.UNSIGNED_BYTE,ee);return Z}let Y={};Y[i.TEXTURE_2D]=Fe(i.TEXTURE_2D,i.TEXTURE_2D,1),Y[i.TEXTURE_CUBE_MAP]=Fe(i.TEXTURE_CUBE_MAP,i.TEXTURE_CUBE_MAP_POSITIVE_X,6),Y[i.TEXTURE_2D_ARRAY]=Fe(i.TEXTURE_2D_ARRAY,i.TEXTURE_2D_ARRAY,1,1),Y[i.TEXTURE_3D]=Fe(i.TEXTURE_3D,i.TEXTURE_3D,1,1),s.setClear(0,0,0,1),a.setClear(1),o.setClear(0),J(i.DEPTH_TEST),a.setFunc(Mi),Ie(!1),ye(Al),J(i.CULL_FACE),ot(Xn);function J(L){d[L]!==!0&&(i.enable(L),d[L]=!0)}function pe(L){d[L]!==!1&&(i.disable(L),d[L]=!1)}function Ce(L,re){return u[L]!==re?(i.bindFramebuffer(L,re),u[L]=re,L===i.DRAW_FRAMEBUFFER&&(u[i.FRAMEBUFFER]=re),L===i.FRAMEBUFFER&&(u[i.DRAW_FRAMEBUFFER]=re),!0):!1}function ge(L,re){let ae=p,me=!1;if(L){ae=h.get(re),ae===void 0&&(ae=[],h.set(re,ae));let ee=L.textures;if(ae.length!==ee.length||ae[0]!==i.COLOR_ATTACHMENT0){for(let Z=0,_e=ee.length;Z<_e;Z++)ae[Z]=i.COLOR_ATTACHMENT0+Z;ae.length=ee.length,me=!0}}else ae[0]!==i.BACK&&(ae[0]=i.BACK,me=!0);me&&i.drawBuffers(ae)}function ze(L){return g!==L?(i.useProgram(L),g=L,!0):!1}let xt={[ri]:i.FUNC_ADD,[xd]:i.FUNC_SUBTRACT,[_d]:i.FUNC_REVERSE_SUBTRACT};xt[yd]=i.MIN,xt[vd]=i.MAX;let I={[bd]:i.ZERO,[wd]:i.ONE,[Md]:i.SRC_COLOR,[aa]:i.SRC_ALPHA,[Rd]:i.SRC_ALPHA_SATURATE,[Ad]:i.DST_COLOR,[Ed]:i.DST_ALPHA,[Sd]:i.ONE_MINUS_SRC_COLOR,[oa]:i.ONE_MINUS_SRC_ALPHA,[Cd]:i.ONE_MINUS_DST_COLOR,[Td]:i.ONE_MINUS_DST_ALPHA,[Id]:i.CONSTANT_COLOR,[Pd]:i.ONE_MINUS_CONSTANT_COLOR,[Nd]:i.CONSTANT_ALPHA,[Dd]:i.ONE_MINUS_CONSTANT_ALPHA};function ot(L,re,ae,me,ee,Z,_e,Le,nt,Ye){if(L===Xn){x===!0&&(pe(i.BLEND),x=!1);return}if(x===!1&&(J(i.BLEND),x=!0),L!==gd){if(L!==m||Ye!==w){if((f!==ri||y!==ri)&&(i.blendEquation(i.FUNC_ADD),f=ri,y=ri),Ye)switch(L){case wi:i.blendFuncSeparate(i.ONE,i.ONE_MINUS_SRC_ALPHA,i.ONE,i.ONE_MINUS_SRC_ALPHA);break;case Rl:i.blendFunc(i.ONE,i.ONE);break;case Il:i.blendFuncSeparate(i.ZERO,i.ONE_MINUS_SRC_COLOR,i.ZERO,i.ONE);break;case Pl:i.blendFuncSeparate(i.DST_COLOR,i.ONE_MINUS_SRC_ALPHA,i.ZERO,i.ONE);break;default:console.error("THREE.WebGLState: Invalid blending: ",L);break}else switch(L){case wi:i.blendFuncSeparate(i.SRC_ALPHA,i.ONE_MINUS_SRC_ALPHA,i.ONE,i.ONE_MINUS_SRC_ALPHA);break;case Rl:i.blendFuncSeparate(i.SRC_ALPHA,i.ONE,i.ONE,i.ONE);break;case Il:console.error("THREE.WebGLState: SubtractiveBlending requires material.premultipliedAlpha = true");break;case Pl:console.error("THREE.WebGLState: MultiplyBlending requires material.premultipliedAlpha = true");break;default:console.error("THREE.WebGLState: Invalid blending: ",L);break}S=null,M=null,C=null,E=null,R.set(0,0,0),P=0,m=L,w=Ye}return}ee=ee||re,Z=Z||ae,_e=_e||me,(re!==f||ee!==y)&&(i.blendEquationSeparate(xt[re],xt[ee]),f=re,y=ee),(ae!==S||me!==M||Z!==C||_e!==E)&&(i.blendFuncSeparate(I[ae],I[me],I[Z],I[_e]),S=ae,M=me,C=Z,E=_e),(Le.equals(R)===!1||nt!==P)&&(i.blendColor(Le.r,Le.g,Le.b,nt),R.copy(Le),P=nt),m=L,w=!1}function Ue(L,re){L.side===dn?pe(i.CULL_FACE):J(i.CULL_FACE);let ae=L.side===zt;re&&(ae=!ae),Ie(ae),L.blending===wi&&L.transparent===!1?ot(Xn):ot(L.blending,L.blendEquation,L.blendSrc,L.blendDst,L.blendEquationAlpha,L.blendSrcAlpha,L.blendDstAlpha,L.blendColor,L.blendAlpha,L.premultipliedAlpha),a.setFunc(L.depthFunc),a.setTest(L.depthTest),a.setMask(L.depthWrite),s.setMask(L.colorWrite);let me=L.stencilWrite;o.setTest(me),me&&(o.setMask(L.stencilWriteMask),o.setFunc(L.stencilFunc,L.stencilRef,L.stencilFuncMask),o.setOp(L.stencilFail,L.stencilZFail,L.stencilZPass)),ve(L.polygonOffset,L.polygonOffsetFactor,L.polygonOffsetUnits),L.alphaToCoverage===!0?J(i.SAMPLE_ALPHA_TO_COVERAGE):pe(i.SAMPLE_ALPHA_TO_COVERAGE)}function Ie(L){v!==L&&(L?i.frontFace(i.CW):i.frontFace(i.CCW),v=L)}function ye(L){L!==fd?(J(i.CULL_FACE),L!==T&&(L===Al?i.cullFace(i.BACK):L===pd?i.cullFace(i.FRONT):i.cullFace(i.FRONT_AND_BACK))):pe(i.CULL_FACE),T=L}function lt(L){L!==D&&(W&&i.lineWidth(L),D=L)}function ve(L,re,ae){L?(J(i.POLYGON_OFFSET_FILL),(F!==re||B!==ae)&&(i.polygonOffset(re,ae),F=re,B=ae)):pe(i.POLYGON_OFFSET_FILL)}function ke(L){L?J(i.SCISSOR_TEST):pe(i.SCISSOR_TEST)}function At(L){L===void 0&&(L=i.TEXTURE0+k-1),Q!==L&&(i.activeTexture(L),Q=L)}function vt(L,re,ae){ae===void 0&&(Q===null?ae=i.TEXTURE0+k-1:ae=Q);let me=ne[ae];me===void 0&&(me={type:void 0,texture:void 0},ne[ae]=me),(me.type!==L||me.texture!==re)&&(Q!==ae&&(i.activeTexture(ae),Q=ae),i.bindTexture(L,re||Y[L]),me.type=L,me.texture=re)}function A(){let L=ne[Q];L!==void 0&&L.type!==void 0&&(i.bindTexture(L.type,null),L.type=void 0,L.texture=void 0)}function _(){try{i.compressedTexImage2D(...arguments)}catch(L){console.error("THREE.WebGLState:",L)}}function z(){try{i.compressedTexImage3D(...arguments)}catch(L){console.error("THREE.WebGLState:",L)}}function q(){try{i.texSubImage2D(...arguments)}catch(L){console.error("THREE.WebGLState:",L)}}function K(){try{i.texSubImage3D(...arguments)}catch(L){console.error("THREE.WebGLState:",L)}}function $(){try{i.compressedTexSubImage2D(...arguments)}catch(L){console.error("THREE.WebGLState:",L)}}function Se(){try{i.compressedTexSubImage3D(...arguments)}catch(L){console.error("THREE.WebGLState:",L)}}function se(){try{i.texStorage2D(...arguments)}catch(L){console.error("THREE.WebGLState:",L)}}function be(){try{i.texStorage3D(...arguments)}catch(L){console.error("THREE.WebGLState:",L)}}function we(){try{i.texImage2D(...arguments)}catch(L){console.error("THREE.WebGLState:",L)}}function ie(){try{i.texImage3D(...arguments)}catch(L){console.error("THREE.WebGLState:",L)}}function de(L){Xe.equals(L)===!1&&(i.scissor(L.x,L.y,L.z,L.w),Xe.copy(L))}function Re(L){Ze.equals(L)===!1&&(i.viewport(L.x,L.y,L.z,L.w),Ze.copy(L))}function Me(L,re){let ae=c.get(re);ae===void 0&&(ae=new WeakMap,c.set(re,ae));let me=ae.get(L);me===void 0&&(me=i.getUniformBlockIndex(re,L.name),ae.set(L,me))}function le(L,re){let me=c.get(re).get(L);l.get(re)!==me&&(i.uniformBlockBinding(re,me,L.__bindingPointIndex),l.set(re,me))}function Be(){i.disable(i.BLEND),i.disable(i.CULL_FACE),i.disable(i.DEPTH_TEST),i.disable(i.POLYGON_OFFSET_FILL),i.disable(i.SCISSOR_TEST),i.disable(i.STENCIL_TEST),i.disable(i.SAMPLE_ALPHA_TO_COVERAGE),i.blendEquation(i.FUNC_ADD),i.blendFunc(i.ONE,i.ZERO),i.blendFuncSeparate(i.ONE,i.ZERO,i.ONE,i.ZERO),i.blendColor(0,0,0,0),i.colorMask(!0,!0,!0,!0),i.clearColor(0,0,0,0),i.depthMask(!0),i.depthFunc(i.LESS),a.setReversed(!1),i.clearDepth(1),i.stencilMask(4294967295),i.stencilFunc(i.ALWAYS,0,4294967295),i.stencilOp(i.KEEP,i.KEEP,i.KEEP),i.clearStencil(0),i.cullFace(i.BACK),i.frontFace(i.CCW),i.polygonOffset(0,0),i.activeTexture(i.TEXTURE0),i.bindFramebuffer(i.FRAMEBUFFER,null),i.bindFramebuffer(i.DRAW_FRAMEBUFFER,null),i.bindFramebuffer(i.READ_FRAMEBUFFER,null),i.useProgram(null),i.lineWidth(1),i.scissor(0,0,i.canvas.width,i.canvas.height),i.viewport(0,0,i.canvas.width,i.canvas.height),d={},Q=null,ne={},u={},h=new WeakMap,p=[],g=null,x=!1,m=null,f=null,S=null,M=null,y=null,C=null,E=null,R=new Ne(0,0,0),P=0,w=!1,v=null,T=null,D=null,F=null,B=null,Xe.set(0,0,i.canvas.width,i.canvas.height),Ze.set(0,0,i.canvas.width,i.canvas.height),s.reset(),a.reset(),o.reset()}return{buffers:{color:s,depth:a,stencil:o},enable:J,disable:pe,bindFramebuffer:Ce,drawBuffers:ge,useProgram:ze,setBlending:ot,setMaterial:Ue,setFlipSided:Ie,setCullFace:ye,setLineWidth:lt,setPolygonOffset:ve,setScissorTest:ke,activeTexture:At,bindTexture:vt,unbindTexture:A,compressedTexImage2D:_,compressedTexImage3D:z,texImage2D:we,texImage3D:ie,updateUBOMapping:Me,uniformBlockBinding:le,texStorage2D:se,texStorage3D:be,texSubImage2D:q,texSubImage3D:K,compressedTexSubImage2D:$,compressedTexSubImage3D:Se,scissor:de,viewport:Re,reset:Be}}function V0(i,e,t,n,r,s,a){let o=e.has("WEBGL_multisampled_render_to_texture")?e.get("WEBGL_multisampled_render_to_texture"):null,l=typeof navigator>"u"?!1:/OculusBrowser/g.test(navigator.userAgent),c=new He,d=new WeakMap,u,h=new WeakMap,p=!1;try{p=typeof OffscreenCanvas<"u"&&new OffscreenCanvas(1,1).getContext("2d")!==null}catch{}function g(A,_){return p?new OffscreenCanvas(A,_):Vr("canvas")}function x(A,_,z){let q=1,K=vt(A);if((K.width>z||K.height>z)&&(q=z/Math.max(K.width,K.height)),q<1)if(typeof HTMLImageElement<"u"&&A instanceof HTMLImageElement||typeof HTMLCanvasElement<"u"&&A instanceof HTMLCanvasElement||typeof ImageBitmap<"u"&&A instanceof ImageBitmap||typeof VideoFrame<"u"&&A instanceof VideoFrame){let $=Math.floor(q*K.width),Se=Math.floor(q*K.height);u===void 0&&(u=g($,Se));let se=_?g($,Se):u;return se.width=$,se.height=Se,se.getContext("2d").drawImage(A,0,0,$,Se),console.warn("THREE.WebGLRenderer: Texture has been resized from ("+K.width+"x"+K.height+") to ("+$+"x"+Se+")."),se}else return"data"in A&&console.warn("THREE.WebGLRenderer: Image in DataTexture is too big ("+K.width+"x"+K.height+")."),A;return A}function m(A){return A.generateMipmaps}function f(A){i.generateMipmap(A)}function S(A){return A.isWebGLCubeRenderTarget?i.TEXTURE_CUBE_MAP:A.isWebGL3DRenderTarget?i.TEXTURE_3D:A.isWebGLArrayRenderTarget||A.isCompressedArrayTexture?i.TEXTURE_2D_ARRAY:i.TEXTURE_2D}function M(A,_,z,q,K=!1){if(A!==null){if(i[A]!==void 0)return i[A];console.warn("THREE.WebGLRenderer: Attempt to use non-existing WebGL internal format '"+A+"'")}let $=_;if(_===i.RED&&(z===i.FLOAT&&($=i.R32F),z===i.HALF_FLOAT&&($=i.R16F),z===i.UNSIGNED_BYTE&&($=i.R8)),_===i.RED_INTEGER&&(z===i.UNSIGNED_BYTE&&($=i.R8UI),z===i.UNSIGNED_SHORT&&($=i.R16UI),z===i.UNSIGNED_INT&&($=i.R32UI),z===i.BYTE&&($=i.R8I),z===i.SHORT&&($=i.R16I),z===i.INT&&($=i.R32I)),_===i.RG&&(z===i.FLOAT&&($=i.RG32F),z===i.HALF_FLOAT&&($=i.RG16F),z===i.UNSIGNED_BYTE&&($=i.RG8)),_===i.RG_INTEGER&&(z===i.UNSIGNED_BYTE&&($=i.RG8UI),z===i.UNSIGNED_SHORT&&($=i.RG16UI),z===i.UNSIGNED_INT&&($=i.RG32UI),z===i.BYTE&&($=i.RG8I),z===i.SHORT&&($=i.RG16I),z===i.INT&&($=i.RG32I)),_===i.RGB_INTEGER&&(z===i.UNSIGNED_BYTE&&($=i.RGB8UI),z===i.UNSIGNED_SHORT&&($=i.RGB16UI),z===i.UNSIGNED_INT&&($=i.RGB32UI),z===i.BYTE&&($=i.RGB8I),z===i.SHORT&&($=i.RGB16I),z===i.INT&&($=i.RGB32I)),_===i.RGBA_INTEGER&&(z===i.UNSIGNED_BYTE&&($=i.RGBA8UI),z===i.UNSIGNED_SHORT&&($=i.RGBA16UI),z===i.UNSIGNED_INT&&($=i.RGBA32UI),z===i.BYTE&&($=i.RGBA8I),z===i.SHORT&&($=i.RGBA16I),z===i.INT&&($=i.RGBA32I)),_===i.RGB&&(z===i.UNSIGNED_INT_5_9_9_9_REV&&($=i.RGB9_E5),z===i.UNSIGNED_INT_10F_11F_11F_REV&&($=i.R11F_G11F_B10F)),_===i.RGBA){let Se=K?kr:$e.getTransfer(q);z===i.FLOAT&&($=i.RGBA32F),z===i.HALF_FLOAT&&($=i.RGBA16F),z===i.UNSIGNED_BYTE&&($=Se===Ke?i.SRGB8_ALPHA8:i.RGBA8),z===i.UNSIGNED_SHORT_4_4_4_4&&($=i.RGBA4),z===i.UNSIGNED_SHORT_5_5_5_1&&($=i.RGB5_A1)}return($===i.R16F||$===i.R32F||$===i.RG16F||$===i.RG32F||$===i.RGBA16F||$===i.RGBA32F)&&e.get("EXT_color_buffer_float"),$}function y(A,_){let z;return A?_===null||_===hi||_===_r?z=i.DEPTH24_STENCIL8:_===Pn?z=i.DEPTH32F_STENCIL8:_===gr&&(z=i.DEPTH24_STENCIL8,console.warn("DepthTexture: 16 bit depth attachment is not supported with stencil. Using 24-bit attachment.")):_===null||_===hi||_===_r?z=i.DEPTH_COMPONENT24:_===Pn?z=i.DEPTH_COMPONENT32F:_===gr&&(z=i.DEPTH_COMPONENT16),z}function C(A,_){return m(A)===!0||A.isFramebufferTexture&&A.minFilter!==cn&&A.minFilter!==vn?Math.log2(Math.max(_.width,_.height))+1:A.mipmaps!==void 0&&A.mipmaps.length>0?A.mipmaps.length:A.isCompressedTexture&&Array.isArray(A.image)?_.mipmaps.length:1}function E(A){let _=A.target;_.removeEventListener("dispose",E),P(_),_.isVideoTexture&&d.delete(_)}function R(A){let _=A.target;_.removeEventListener("dispose",R),v(_)}function P(A){let _=n.get(A);if(_.__webglInit===void 0)return;let z=A.source,q=h.get(z);if(q){let K=q[_.__cacheKey];K.usedTimes--,K.usedTimes===0&&w(A),Object.keys(q).length===0&&h.delete(z)}n.remove(A)}function w(A){let _=n.get(A);i.deleteTexture(_.__webglTexture);let z=A.source,q=h.get(z);delete q[_.__cacheKey],a.memory.textures--}function v(A){let _=n.get(A);if(A.depthTexture&&(A.depthTexture.dispose(),n.remove(A.depthTexture)),A.isWebGLCubeRenderTarget)for(let q=0;q<6;q++){if(Array.isArray(_.__webglFramebuffer[q]))for(let K=0;K<_.__webglFramebuffer[q].length;K++)i.deleteFramebuffer(_.__webglFramebuffer[q][K]);else i.deleteFramebuffer(_.__webglFramebuffer[q]);_.__webglDepthbuffer&&i.deleteRenderbuffer(_.__webglDepthbuffer[q])}else{if(Array.isArray(_.__webglFramebuffer))for(let q=0;q<_.__webglFramebuffer.length;q++)i.deleteFramebuffer(_.__webglFramebuffer[q]);else i.deleteFramebuffer(_.__webglFramebuffer);if(_.__webglDepthbuffer&&i.deleteRenderbuffer(_.__webglDepthbuffer),_.__webglMultisampledFramebuffer&&i.deleteFramebuffer(_.__webglMultisampledFramebuffer),_.__webglColorRenderbuffer)for(let q=0;q<_.__webglColorRenderbuffer.length;q++)_.__webglColorRenderbuffer[q]&&i.deleteRenderbuffer(_.__webglColorRenderbuffer[q]);_.__webglDepthRenderbuffer&&i.deleteRenderbuffer(_.__webglDepthRenderbuffer)}let z=A.textures;for(let q=0,K=z.length;q<K;q++){let $=n.get(z[q]);$.__webglTexture&&(i.deleteTexture($.__webglTexture),a.memory.textures--),n.remove(z[q])}n.remove(A)}let T=0;function D(){T=0}function F(){let A=T;return A>=r.maxTextures&&console.warn("THREE.WebGLTextures: Trying to use "+A+" texture units while this GPU supports only "+r.maxTextures),T+=1,A}function B(A){let _=[];return _.push(A.wrapS),_.push(A.wrapT),_.push(A.wrapR||0),_.push(A.magFilter),_.push(A.minFilter),_.push(A.anisotropy),_.push(A.internalFormat),_.push(A.format),_.push(A.type),_.push(A.generateMipmaps),_.push(A.premultiplyAlpha),_.push(A.flipY),_.push(A.unpackAlignment),_.push(A.colorSpace),_.join()}function k(A,_){let z=n.get(A);if(A.isVideoTexture&&ke(A),A.isRenderTargetTexture===!1&&A.isExternalTexture!==!0&&A.version>0&&z.__version!==A.version){let q=A.image;if(q===null)console.warn("THREE.WebGLRenderer: Texture marked for update but no image data found.");else if(q.complete===!1)console.warn("THREE.WebGLRenderer: Texture marked for update but image is incomplete");else{Y(z,A,_);return}}else A.isExternalTexture&&(z.__webglTexture=A.sourceTexture?A.sourceTexture:null);t.bindTexture(i.TEXTURE_2D,z.__webglTexture,i.TEXTURE0+_)}function W(A,_){let z=n.get(A);if(A.isRenderTargetTexture===!1&&A.version>0&&z.__version!==A.version){Y(z,A,_);return}t.bindTexture(i.TEXTURE_2D_ARRAY,z.__webglTexture,i.TEXTURE0+_)}function X(A,_){let z=n.get(A);if(A.isRenderTargetTexture===!1&&A.version>0&&z.__version!==A.version){Y(z,A,_);return}t.bindTexture(i.TEXTURE_3D,z.__webglTexture,i.TEXTURE0+_)}function H(A,_){let z=n.get(A);if(A.version>0&&z.__version!==A.version){J(z,A,_);return}t.bindTexture(i.TEXTURE_CUBE_MAP,z.__webglTexture,i.TEXTURE0+_)}let Q={[la]:i.REPEAT,[ii]:i.CLAMP_TO_EDGE,[ca]:i.MIRRORED_REPEAT},ne={[cn]:i.NEAREST,[Gd]:i.NEAREST_MIPMAP_NEAREST,[fs]:i.NEAREST_MIPMAP_LINEAR,[vn]:i.LINEAR,[Va]:i.LINEAR_MIPMAP_NEAREST,[ui]:i.LINEAR_MIPMAP_LINEAR},fe={[qd]:i.NEVER,[Qd]:i.ALWAYS,[Yd]:i.LESS,[Gl]:i.LEQUAL,[Zd]:i.EQUAL,[jd]:i.GEQUAL,[Jd]:i.GREATER,[Kd]:i.NOTEQUAL};function De(A,_){if(_.type===Pn&&e.has("OES_texture_float_linear")===!1&&(_.magFilter===vn||_.magFilter===Va||_.magFilter===fs||_.magFilter===ui||_.minFilter===vn||_.minFilter===Va||_.minFilter===fs||_.minFilter===ui)&&console.warn("THREE.WebGLRenderer: Unable to use linear filtering with floating point textures. OES_texture_float_linear not supported on this device."),i.texParameteri(A,i.TEXTURE_WRAP_S,Q[_.wrapS]),i.texParameteri(A,i.TEXTURE_WRAP_T,Q[_.wrapT]),(A===i.TEXTURE_3D||A===i.TEXTURE_2D_ARRAY)&&i.texParameteri(A,i.TEXTURE_WRAP_R,Q[_.wrapR]),i.texParameteri(A,i.TEXTURE_MAG_FILTER,ne[_.magFilter]),i.texParameteri(A,i.TEXTURE_MIN_FILTER,ne[_.minFilter]),_.compareFunction&&(i.texParameteri(A,i.TEXTURE_COMPARE_MODE,i.COMPARE_REF_TO_TEXTURE),i.texParameteri(A,i.TEXTURE_COMPARE_FUNC,fe[_.compareFunction])),e.has("EXT_texture_filter_anisotropic")===!0){if(_.magFilter===cn||_.minFilter!==fs&&_.minFilter!==ui||_.type===Pn&&e.has("OES_texture_float_linear")===!1)return;if(_.anisotropy>1||n.get(_).__currentAnisotropy){let z=e.get("EXT_texture_filter_anisotropic");i.texParameterf(A,z.TEXTURE_MAX_ANISOTROPY_EXT,Math.min(_.anisotropy,r.getMaxAnisotropy())),n.get(_).__currentAnisotropy=_.anisotropy}}}function Xe(A,_){let z=!1;A.__webglInit===void 0&&(A.__webglInit=!0,_.addEventListener("dispose",E));let q=_.source,K=h.get(q);K===void 0&&(K={},h.set(q,K));let $=B(_);if($!==A.__cacheKey){K[$]===void 0&&(K[$]={texture:i.createTexture(),usedTimes:0},a.memory.textures++,z=!0),K[$].usedTimes++;let Se=K[A.__cacheKey];Se!==void 0&&(K[A.__cacheKey].usedTimes--,Se.usedTimes===0&&w(_)),A.__cacheKey=$,A.__webglTexture=K[$].texture}return z}function Ze(A,_,z){return Math.floor(Math.floor(A/z)/_)}function Fe(A,_,z,q){let $=A.updateRanges;if($.length===0)t.texSubImage2D(i.TEXTURE_2D,0,0,0,_.width,_.height,z,q,_.data);else{$.sort((ie,de)=>ie.start-de.start);let Se=0;for(let ie=1;ie<$.length;ie++){let de=$[Se],Re=$[ie],Me=de.start+de.count,le=Ze(Re.start,_.width,4),Be=Ze(de.start,_.width,4);Re.start<=Me+1&&le===Be&&Ze(Re.start+Re.count-1,_.width,4)===le?de.count=Math.max(de.count,Re.start+Re.count-de.start):(++Se,$[Se]=Re)}$.length=Se+1;let se=i.getParameter(i.UNPACK_ROW_LENGTH),be=i.getParameter(i.UNPACK_SKIP_PIXELS),we=i.getParameter(i.UNPACK_SKIP_ROWS);i.pixelStorei(i.UNPACK_ROW_LENGTH,_.width);for(let ie=0,de=$.length;ie<de;ie++){let Re=$[ie],Me=Math.floor(Re.start/4),le=Math.ceil(Re.count/4),Be=Me%_.width,L=Math.floor(Me/_.width),re=le,ae=1;i.pixelStorei(i.UNPACK_SKIP_PIXELS,Be),i.pixelStorei(i.UNPACK_SKIP_ROWS,L),t.texSubImage2D(i.TEXTURE_2D,0,Be,L,re,ae,z,q,_.data)}A.clearUpdateRanges(),i.pixelStorei(i.UNPACK_ROW_LENGTH,se),i.pixelStorei(i.UNPACK_SKIP_PIXELS,be),i.pixelStorei(i.UNPACK_SKIP_ROWS,we)}}function Y(A,_,z){let q=i.TEXTURE_2D;(_.isDataArrayTexture||_.isCompressedArrayTexture)&&(q=i.TEXTURE_2D_ARRAY),_.isData3DTexture&&(q=i.TEXTURE_3D);let K=Xe(A,_),$=_.source;t.bindTexture(q,A.__webglTexture,i.TEXTURE0+z);let Se=n.get($);if($.version!==Se.__version||K===!0){t.activeTexture(i.TEXTURE0+z);let se=$e.getPrimaries($e.workingColorSpace),be=_.colorSpace===qn?null:$e.getPrimaries(_.colorSpace),we=_.colorSpace===qn||se===be?i.NONE:i.BROWSER_DEFAULT_WEBGL;i.pixelStorei(i.UNPACK_FLIP_Y_WEBGL,_.flipY),i.pixelStorei(i.UNPACK_PREMULTIPLY_ALPHA_WEBGL,_.premultiplyAlpha),i.pixelStorei(i.UNPACK_ALIGNMENT,_.unpackAlignment),i.pixelStorei(i.UNPACK_COLORSPACE_CONVERSION_WEBGL,we);let ie=x(_.image,!1,r.maxTextureSize);ie=At(_,ie);let de=s.convert(_.format,_.colorSpace),Re=s.convert(_.type),Me=M(_.internalFormat,de,Re,_.colorSpace,_.isVideoTexture);De(q,_);let le,Be=_.mipmaps,L=_.isVideoTexture!==!0,re=Se.__version===void 0||K===!0,ae=$.dataReady,me=C(_,ie);if(_.isDepthTexture)Me=y(_.format===yr,_.type),re&&(L?t.texStorage2D(i.TEXTURE_2D,1,Me,ie.width,ie.height):t.texImage2D(i.TEXTURE_2D,0,Me,ie.width,ie.height,0,de,Re,null));else if(_.isDataTexture)if(Be.length>0){L&&re&&t.texStorage2D(i.TEXTURE_2D,me,Me,Be[0].width,Be[0].height);for(let ee=0,Z=Be.length;ee<Z;ee++)le=Be[ee],L?ae&&t.texSubImage2D(i.TEXTURE_2D,ee,0,0,le.width,le.height,de,Re,le.data):t.texImage2D(i.TEXTURE_2D,ee,Me,le.width,le.height,0,de,Re,le.data);_.generateMipmaps=!1}else L?(re&&t.texStorage2D(i.TEXTURE_2D,me,Me,ie.width,ie.height),ae&&Fe(_,ie,de,Re)):t.texImage2D(i.TEXTURE_2D,0,Me,ie.width,ie.height,0,de,Re,ie.data);else if(_.isCompressedTexture)if(_.isCompressedArrayTexture){L&&re&&t.texStorage3D(i.TEXTURE_2D_ARRAY,me,Me,Be[0].width,Be[0].height,ie.depth);for(let ee=0,Z=Be.length;ee<Z;ee++)if(le=Be[ee],_.format!==un)if(de!==null)if(L){if(ae)if(_.layerUpdates.size>0){let _e=Jl(le.width,le.height,_.format,_.type);for(let Le of _.layerUpdates){let nt=le.data.subarray(Le*_e/le.data.BYTES_PER_ELEMENT,(Le+1)*_e/le.data.BYTES_PER_ELEMENT);t.compressedTexSubImage3D(i.TEXTURE_2D_ARRAY,ee,0,0,Le,le.width,le.height,1,de,nt)}_.clearLayerUpdates()}else t.compressedTexSubImage3D(i.TEXTURE_2D_ARRAY,ee,0,0,0,le.width,le.height,ie.depth,de,le.data)}else t.compressedTexImage3D(i.TEXTURE_2D_ARRAY,ee,Me,le.width,le.height,ie.depth,0,le.data,0,0);else console.warn("THREE.WebGLRenderer: Attempt to load unsupported compressed texture format in .uploadTexture()");else L?ae&&t.texSubImage3D(i.TEXTURE_2D_ARRAY,ee,0,0,0,le.width,le.height,ie.depth,de,Re,le.data):t.texImage3D(i.TEXTURE_2D_ARRAY,ee,Me,le.width,le.height,ie.depth,0,de,Re,le.data)}else{L&&re&&t.texStorage2D(i.TEXTURE_2D,me,Me,Be[0].width,Be[0].height);for(let ee=0,Z=Be.length;ee<Z;ee++)le=Be[ee],_.format!==un?de!==null?L?ae&&t.compressedTexSubImage2D(i.TEXTURE_2D,ee,0,0,le.width,le.height,de,le.data):t.compressedTexImage2D(i.TEXTURE_2D,ee,Me,le.width,le.height,0,le.data):console.warn("THREE.WebGLRenderer: Attempt to load unsupported compressed texture format in .uploadTexture()"):L?ae&&t.texSubImage2D(i.TEXTURE_2D,ee,0,0,le.width,le.height,de,Re,le.data):t.texImage2D(i.TEXTURE_2D,ee,Me,le.width,le.height,0,de,Re,le.data)}else if(_.isDataArrayTexture)if(L){if(re&&t.texStorage3D(i.TEXTURE_2D_ARRAY,me,Me,ie.width,ie.height,ie.depth),ae)if(_.layerUpdates.size>0){let ee=Jl(ie.width,ie.height,_.format,_.type);for(let Z of _.layerUpdates){let _e=ie.data.subarray(Z*ee/ie.data.BYTES_PER_ELEMENT,(Z+1)*ee/ie.data.BYTES_PER_ELEMENT);t.texSubImage3D(i.TEXTURE_2D_ARRAY,0,0,0,Z,ie.width,ie.height,1,de,Re,_e)}_.clearLayerUpdates()}else t.texSubImage3D(i.TEXTURE_2D_ARRAY,0,0,0,0,ie.width,ie.height,ie.depth,de,Re,ie.data)}else t.texImage3D(i.TEXTURE_2D_ARRAY,0,Me,ie.width,ie.height,ie.depth,0,de,Re,ie.data);else if(_.isData3DTexture)L?(re&&t.texStorage3D(i.TEXTURE_3D,me,Me,ie.width,ie.height,ie.depth),ae&&t.texSubImage3D(i.TEXTURE_3D,0,0,0,0,ie.width,ie.height,ie.depth,de,Re,ie.data)):t.texImage3D(i.TEXTURE_3D,0,Me,ie.width,ie.height,ie.depth,0,de,Re,ie.data);else if(_.isFramebufferTexture){if(re)if(L)t.texStorage2D(i.TEXTURE_2D,me,Me,ie.width,ie.height);else{let ee=ie.width,Z=ie.height;for(let _e=0;_e<me;_e++)t.texImage2D(i.TEXTURE_2D,_e,Me,ee,Z,0,de,Re,null),ee>>=1,Z>>=1}}else if(Be.length>0){if(L&&re){let ee=vt(Be[0]);t.texStorage2D(i.TEXTURE_2D,me,Me,ee.width,ee.height)}for(let ee=0,Z=Be.length;ee<Z;ee++)le=Be[ee],L?ae&&t.texSubImage2D(i.TEXTURE_2D,ee,0,0,de,Re,le):t.texImage2D(i.TEXTURE_2D,ee,Me,de,Re,le);_.generateMipmaps=!1}else if(L){if(re){let ee=vt(ie);t.texStorage2D(i.TEXTURE_2D,me,Me,ee.width,ee.height)}ae&&t.texSubImage2D(i.TEXTURE_2D,0,0,0,de,Re,ie)}else t.texImage2D(i.TEXTURE_2D,0,Me,de,Re,ie);m(_)&&f(q),Se.__version=$.version,_.onUpdate&&_.onUpdate(_)}A.__version=_.version}function J(A,_,z){if(_.image.length!==6)return;let q=Xe(A,_),K=_.source;t.bindTexture(i.TEXTURE_CUBE_MAP,A.__webglTexture,i.TEXTURE0+z);let $=n.get(K);if(K.version!==$.__version||q===!0){t.activeTexture(i.TEXTURE0+z);let Se=$e.getPrimaries($e.workingColorSpace),se=_.colorSpace===qn?null:$e.getPrimaries(_.colorSpace),be=_.colorSpace===qn||Se===se?i.NONE:i.BROWSER_DEFAULT_WEBGL;i.pixelStorei(i.UNPACK_FLIP_Y_WEBGL,_.flipY),i.pixelStorei(i.UNPACK_PREMULTIPLY_ALPHA_WEBGL,_.premultiplyAlpha),i.pixelStorei(i.UNPACK_ALIGNMENT,_.unpackAlignment),i.pixelStorei(i.UNPACK_COLORSPACE_CONVERSION_WEBGL,be);let we=_.isCompressedTexture||_.image[0].isCompressedTexture,ie=_.image[0]&&_.image[0].isDataTexture,de=[];for(let Z=0;Z<6;Z++)!we&&!ie?de[Z]=x(_.image[Z],!0,r.maxCubemapSize):de[Z]=ie?_.image[Z].image:_.image[Z],de[Z]=At(_,de[Z]);let Re=de[0],Me=s.convert(_.format,_.colorSpace),le=s.convert(_.type),Be=M(_.internalFormat,Me,le,_.colorSpace),L=_.isVideoTexture!==!0,re=$.__version===void 0||q===!0,ae=K.dataReady,me=C(_,Re);De(i.TEXTURE_CUBE_MAP,_);let ee;if(we){L&&re&&t.texStorage2D(i.TEXTURE_CUBE_MAP,me,Be,Re.width,Re.height);for(let Z=0;Z<6;Z++){ee=de[Z].mipmaps;for(let _e=0;_e<ee.length;_e++){let Le=ee[_e];_.format!==un?Me!==null?L?ae&&t.compressedTexSubImage2D(i.TEXTURE_CUBE_MAP_POSITIVE_X+Z,_e,0,0,Le.width,Le.height,Me,Le.data):t.compressedTexImage2D(i.TEXTURE_CUBE_MAP_POSITIVE_X+Z,_e,Be,Le.width,Le.height,0,Le.data):console.warn("THREE.WebGLRenderer: Attempt to load unsupported compressed texture format in .setTextureCube()"):L?ae&&t.texSubImage2D(i.TEXTURE_CUBE_MAP_POSITIVE_X+Z,_e,0,0,Le.width,Le.height,Me,le,Le.data):t.texImage2D(i.TEXTURE_CUBE_MAP_POSITIVE_X+Z,_e,Be,Le.width,Le.height,0,Me,le,Le.data)}}}else{if(ee=_.mipmaps,L&&re){ee.length>0&&me++;let Z=vt(de[0]);t.texStorage2D(i.TEXTURE_CUBE_MAP,me,Be,Z.width,Z.height)}for(let Z=0;Z<6;Z++)if(ie){L?ae&&t.texSubImage2D(i.TEXTURE_CUBE_MAP_POSITIVE_X+Z,0,0,0,de[Z].width,de[Z].height,Me,le,de[Z].data):t.texImage2D(i.TEXTURE_CUBE_MAP_POSITIVE_X+Z,0,Be,de[Z].width,de[Z].height,0,Me,le,de[Z].data);for(let _e=0;_e<ee.length;_e++){let nt=ee[_e].image[Z].image;L?ae&&t.texSubImage2D(i.TEXTURE_CUBE_MAP_POSITIVE_X+Z,_e+1,0,0,nt.width,nt.height,Me,le,nt.data):t.texImage2D(i.TEXTURE_CUBE_MAP_POSITIVE_X+Z,_e+1,Be,nt.width,nt.height,0,Me,le,nt.data)}}else{L?ae&&t.texSubImage2D(i.TEXTURE_CUBE_MAP_POSITIVE_X+Z,0,0,0,Me,le,de[Z]):t.texImage2D(i.TEXTURE_CUBE_MAP_POSITIVE_X+Z,0,Be,Me,le,de[Z]);for(let _e=0;_e<ee.length;_e++){let Le=ee[_e];L?ae&&t.texSubImage2D(i.TEXTURE_CUBE_MAP_POSITIVE_X+Z,_e+1,0,0,Me,le,Le.image[Z]):t.texImage2D(i.TEXTURE_CUBE_MAP_POSITIVE_X+Z,_e+1,Be,Me,le,Le.image[Z])}}}m(_)&&f(i.TEXTURE_CUBE_MAP),$.__version=K.version,_.onUpdate&&_.onUpdate(_)}A.__version=_.version}function pe(A,_,z,q,K,$){let Se=s.convert(z.format,z.colorSpace),se=s.convert(z.type),be=M(z.internalFormat,Se,se,z.colorSpace),we=n.get(_),ie=n.get(z);if(ie.__renderTarget=_,!we.__hasExternalTextures){let de=Math.max(1,_.width>>$),Re=Math.max(1,_.height>>$);K===i.TEXTURE_3D||K===i.TEXTURE_2D_ARRAY?t.texImage3D(K,$,be,de,Re,_.depth,0,Se,se,null):t.texImage2D(K,$,be,de,Re,0,Se,se,null)}t.bindFramebuffer(i.FRAMEBUFFER,A),ve(_)?o.framebufferTexture2DMultisampleEXT(i.FRAMEBUFFER,q,K,ie.__webglTexture,0,lt(_)):(K===i.TEXTURE_2D||K>=i.TEXTURE_CUBE_MAP_POSITIVE_X&&K<=i.TEXTURE_CUBE_MAP_NEGATIVE_Z)&&i.framebufferTexture2D(i.FRAMEBUFFER,q,K,ie.__webglTexture,$),t.bindFramebuffer(i.FRAMEBUFFER,null)}function Ce(A,_,z){if(i.bindRenderbuffer(i.RENDERBUFFER,A),_.depthBuffer){let q=_.depthTexture,K=q&&q.isDepthTexture?q.type:null,$=y(_.stencilBuffer,K),Se=_.stencilBuffer?i.DEPTH_STENCIL_ATTACHMENT:i.DEPTH_ATTACHMENT,se=lt(_);ve(_)?o.renderbufferStorageMultisampleEXT(i.RENDERBUFFER,se,$,_.width,_.height):z?i.renderbufferStorageMultisample(i.RENDERBUFFER,se,$,_.width,_.height):i.renderbufferStorage(i.RENDERBUFFER,$,_.width,_.height),i.framebufferRenderbuffer(i.FRAMEBUFFER,Se,i.RENDERBUFFER,A)}else{let q=_.textures;for(let K=0;K<q.length;K++){let $=q[K],Se=s.convert($.format,$.colorSpace),se=s.convert($.type),be=M($.internalFormat,Se,se,$.colorSpace),we=lt(_);z&&ve(_)===!1?i.renderbufferStorageMultisample(i.RENDERBUFFER,we,be,_.width,_.height):ve(_)?o.renderbufferStorageMultisampleEXT(i.RENDERBUFFER,we,be,_.width,_.height):i.renderbufferStorage(i.RENDERBUFFER,be,_.width,_.height)}}i.bindRenderbuffer(i.RENDERBUFFER,null)}function ge(A,_){if(_&&_.isWebGLCubeRenderTarget)throw new Error("Depth Texture with cube render targets is not supported");if(t.bindFramebuffer(i.FRAMEBUFFER,A),!(_.depthTexture&&_.depthTexture.isDepthTexture))throw new Error("renderTarget.depthTexture must be an instance of THREE.DepthTexture");let q=n.get(_.depthTexture);q.__renderTarget=_,(!q.__webglTexture||_.depthTexture.image.width!==_.width||_.depthTexture.image.height!==_.height)&&(_.depthTexture.image.width=_.width,_.depthTexture.image.height=_.height,_.depthTexture.needsUpdate=!0),k(_.depthTexture,0);let K=q.__webglTexture,$=lt(_);if(_.depthTexture.format===or)ve(_)?o.framebufferTexture2DMultisampleEXT(i.FRAMEBUFFER,i.DEPTH_ATTACHMENT,i.TEXTURE_2D,K,0,$):i.framebufferTexture2D(i.FRAMEBUFFER,i.DEPTH_ATTACHMENT,i.TEXTURE_2D,K,0);else if(_.depthTexture.format===yr)ve(_)?o.framebufferTexture2DMultisampleEXT(i.FRAMEBUFFER,i.DEPTH_STENCIL_ATTACHMENT,i.TEXTURE_2D,K,0,$):i.framebufferTexture2D(i.FRAMEBUFFER,i.DEPTH_STENCIL_ATTACHMENT,i.TEXTURE_2D,K,0);else throw new Error("Unknown depthTexture format")}function ze(A){let _=n.get(A),z=A.isWebGLCubeRenderTarget===!0;if(_.__boundDepthTexture!==A.depthTexture){let q=A.depthTexture;if(_.__depthDisposeCallback&&_.__depthDisposeCallback(),q){let K=()=>{delete _.__boundDepthTexture,delete _.__depthDisposeCallback,q.removeEventListener("dispose",K)};q.addEventListener("dispose",K),_.__depthDisposeCallback=K}_.__boundDepthTexture=q}if(A.depthTexture&&!_.__autoAllocateDepthBuffer){if(z)throw new Error("target.depthTexture not supported in Cube render targets");let q=A.texture.mipmaps;q&&q.length>0?ge(_.__webglFramebuffer[0],A):ge(_.__webglFramebuffer,A)}else if(z){_.__webglDepthbuffer=[];for(let q=0;q<6;q++)if(t.bindFramebuffer(i.FRAMEBUFFER,_.__webglFramebuffer[q]),_.__webglDepthbuffer[q]===void 0)_.__webglDepthbuffer[q]=i.createRenderbuffer(),Ce(_.__webglDepthbuffer[q],A,!1);else{let K=A.stencilBuffer?i.DEPTH_STENCIL_ATTACHMENT:i.DEPTH_ATTACHMENT,$=_.__webglDepthbuffer[q];i.bindRenderbuffer(i.RENDERBUFFER,$),i.framebufferRenderbuffer(i.FRAMEBUFFER,K,i.RENDERBUFFER,$)}}else{let q=A.texture.mipmaps;if(q&&q.length>0?t.bindFramebuffer(i.FRAMEBUFFER,_.__webglFramebuffer[0]):t.bindFramebuffer(i.FRAMEBUFFER,_.__webglFramebuffer),_.__webglDepthbuffer===void 0)_.__webglDepthbuffer=i.createRenderbuffer(),Ce(_.__webglDepthbuffer,A,!1);else{let K=A.stencilBuffer?i.DEPTH_STENCIL_ATTACHMENT:i.DEPTH_ATTACHMENT,$=_.__webglDepthbuffer;i.bindRenderbuffer(i.RENDERBUFFER,$),i.framebufferRenderbuffer(i.FRAMEBUFFER,K,i.RENDERBUFFER,$)}}t.bindFramebuffer(i.FRAMEBUFFER,null)}function xt(A,_,z){let q=n.get(A);_!==void 0&&pe(q.__webglFramebuffer,A,A.texture,i.COLOR_ATTACHMENT0,i.TEXTURE_2D,0),z!==void 0&&ze(A)}function I(A){let _=A.texture,z=n.get(A),q=n.get(_);A.addEventListener("dispose",R);let K=A.textures,$=A.isWebGLCubeRenderTarget===!0,Se=K.length>1;if(Se||(q.__webglTexture===void 0&&(q.__webglTexture=i.createTexture()),q.__version=_.version,a.memory.textures++),$){z.__webglFramebuffer=[];for(let se=0;se<6;se++)if(_.mipmaps&&_.mipmaps.length>0){z.__webglFramebuffer[se]=[];for(let be=0;be<_.mipmaps.length;be++)z.__webglFramebuffer[se][be]=i.createFramebuffer()}else z.__webglFramebuffer[se]=i.createFramebuffer()}else{if(_.mipmaps&&_.mipmaps.length>0){z.__webglFramebuffer=[];for(let se=0;se<_.mipmaps.length;se++)z.__webglFramebuffer[se]=i.createFramebuffer()}else z.__webglFramebuffer=i.createFramebuffer();if(Se)for(let se=0,be=K.length;se<be;se++){let we=n.get(K[se]);we.__webglTexture===void 0&&(we.__webglTexture=i.createTexture(),a.memory.textures++)}if(A.samples>0&&ve(A)===!1){z.__webglMultisampledFramebuffer=i.createFramebuffer(),z.__webglColorRenderbuffer=[],t.bindFramebuffer(i.FRAMEBUFFER,z.__webglMultisampledFramebuffer);for(let se=0;se<K.length;se++){let be=K[se];z.__webglColorRenderbuffer[se]=i.createRenderbuffer(),i.bindRenderbuffer(i.RENDERBUFFER,z.__webglColorRenderbuffer[se]);let we=s.convert(be.format,be.colorSpace),ie=s.convert(be.type),de=M(be.internalFormat,we,ie,be.colorSpace,A.isXRRenderTarget===!0),Re=lt(A);i.renderbufferStorageMultisample(i.RENDERBUFFER,Re,de,A.width,A.height),i.framebufferRenderbuffer(i.FRAMEBUFFER,i.COLOR_ATTACHMENT0+se,i.RENDERBUFFER,z.__webglColorRenderbuffer[se])}i.bindRenderbuffer(i.RENDERBUFFER,null),A.depthBuffer&&(z.__webglDepthRenderbuffer=i.createRenderbuffer(),Ce(z.__webglDepthRenderbuffer,A,!0)),t.bindFramebuffer(i.FRAMEBUFFER,null)}}if($){t.bindTexture(i.TEXTURE_CUBE_MAP,q.__webglTexture),De(i.TEXTURE_CUBE_MAP,_);for(let se=0;se<6;se++)if(_.mipmaps&&_.mipmaps.length>0)for(let be=0;be<_.mipmaps.length;be++)pe(z.__webglFramebuffer[se][be],A,_,i.COLOR_ATTACHMENT0,i.TEXTURE_CUBE_MAP_POSITIVE_X+se,be);else pe(z.__webglFramebuffer[se],A,_,i.COLOR_ATTACHMENT0,i.TEXTURE_CUBE_MAP_POSITIVE_X+se,0);m(_)&&f(i.TEXTURE_CUBE_MAP),t.unbindTexture()}else if(Se){for(let se=0,be=K.length;se<be;se++){let we=K[se],ie=n.get(we),de=i.TEXTURE_2D;(A.isWebGL3DRenderTarget||A.isWebGLArrayRenderTarget)&&(de=A.isWebGL3DRenderTarget?i.TEXTURE_3D:i.TEXTURE_2D_ARRAY),t.bindTexture(de,ie.__webglTexture),De(de,we),pe(z.__webglFramebuffer,A,we,i.COLOR_ATTACHMENT0+se,de,0),m(we)&&f(de)}t.unbindTexture()}else{let se=i.TEXTURE_2D;if((A.isWebGL3DRenderTarget||A.isWebGLArrayRenderTarget)&&(se=A.isWebGL3DRenderTarget?i.TEXTURE_3D:i.TEXTURE_2D_ARRAY),t.bindTexture(se,q.__webglTexture),De(se,_),_.mipmaps&&_.mipmaps.length>0)for(let be=0;be<_.mipmaps.length;be++)pe(z.__webglFramebuffer[be],A,_,i.COLOR_ATTACHMENT0,se,be);else pe(z.__webglFramebuffer,A,_,i.COLOR_ATTACHMENT0,se,0);m(_)&&f(se),t.unbindTexture()}A.depthBuffer&&ze(A)}function ot(A){let _=A.textures;for(let z=0,q=_.length;z<q;z++){let K=_[z];if(m(K)){let $=S(A),Se=n.get(K).__webglTexture;t.bindTexture($,Se),f($),t.unbindTexture()}}}let Ue=[],Ie=[];function ye(A){if(A.samples>0){if(ve(A)===!1){let _=A.textures,z=A.width,q=A.height,K=i.COLOR_BUFFER_BIT,$=A.stencilBuffer?i.DEPTH_STENCIL_ATTACHMENT:i.DEPTH_ATTACHMENT,Se=n.get(A),se=_.length>1;if(se)for(let we=0;we<_.length;we++)t.bindFramebuffer(i.FRAMEBUFFER,Se.__webglMultisampledFramebuffer),i.framebufferRenderbuffer(i.FRAMEBUFFER,i.COLOR_ATTACHMENT0+we,i.RENDERBUFFER,null),t.bindFramebuffer(i.FRAMEBUFFER,Se.__webglFramebuffer),i.framebufferTexture2D(i.DRAW_FRAMEBUFFER,i.COLOR_ATTACHMENT0+we,i.TEXTURE_2D,null,0);t.bindFramebuffer(i.READ_FRAMEBUFFER,Se.__webglMultisampledFramebuffer);let be=A.texture.mipmaps;be&&be.length>0?t.bindFramebuffer(i.DRAW_FRAMEBUFFER,Se.__webglFramebuffer[0]):t.bindFramebuffer(i.DRAW_FRAMEBUFFER,Se.__webglFramebuffer);for(let we=0;we<_.length;we++){if(A.resolveDepthBuffer&&(A.depthBuffer&&(K|=i.DEPTH_BUFFER_BIT),A.stencilBuffer&&A.resolveStencilBuffer&&(K|=i.STENCIL_BUFFER_BIT)),se){i.framebufferRenderbuffer(i.READ_FRAMEBUFFER,i.COLOR_ATTACHMENT0,i.RENDERBUFFER,Se.__webglColorRenderbuffer[we]);let ie=n.get(_[we]).__webglTexture;i.framebufferTexture2D(i.DRAW_FRAMEBUFFER,i.COLOR_ATTACHMENT0,i.TEXTURE_2D,ie,0)}i.blitFramebuffer(0,0,z,q,0,0,z,q,K,i.NEAREST),l===!0&&(Ue.length=0,Ie.length=0,Ue.push(i.COLOR_ATTACHMENT0+we),A.depthBuffer&&A.resolveDepthBuffer===!1&&(Ue.push($),Ie.push($),i.invalidateFramebuffer(i.DRAW_FRAMEBUFFER,Ie)),i.invalidateFramebuffer(i.READ_FRAMEBUFFER,Ue))}if(t.bindFramebuffer(i.READ_FRAMEBUFFER,null),t.bindFramebuffer(i.DRAW_FRAMEBUFFER,null),se)for(let we=0;we<_.length;we++){t.bindFramebuffer(i.FRAMEBUFFER,Se.__webglMultisampledFramebuffer),i.framebufferRenderbuffer(i.FRAMEBUFFER,i.COLOR_ATTACHMENT0+we,i.RENDERBUFFER,Se.__webglColorRenderbuffer[we]);let ie=n.get(_[we]).__webglTexture;t.bindFramebuffer(i.FRAMEBUFFER,Se.__webglFramebuffer),i.framebufferTexture2D(i.DRAW_FRAMEBUFFER,i.COLOR_ATTACHMENT0+we,i.TEXTURE_2D,ie,0)}t.bindFramebuffer(i.DRAW_FRAMEBUFFER,Se.__webglMultisampledFramebuffer)}else if(A.depthBuffer&&A.resolveDepthBuffer===!1&&l){let _=A.stencilBuffer?i.DEPTH_STENCIL_ATTACHMENT:i.DEPTH_ATTACHMENT;i.invalidateFramebuffer(i.DRAW_FRAMEBUFFER,[_])}}}function lt(A){return Math.min(r.maxSamples,A.samples)}function ve(A){let _=n.get(A);return A.samples>0&&e.has("WEBGL_multisampled_render_to_texture")===!0&&_.__useRenderToTexture!==!1}function ke(A){let _=a.render.frame;d.get(A)!==_&&(d.set(A,_),A.update())}function At(A,_){let z=A.colorSpace,q=A.format,K=A.type;return A.isCompressedTexture===!0||A.isVideoTexture===!0||z!==Si&&z!==qn&&($e.getTransfer(z)===Ke?(q!==un||K!==Mn)&&console.warn("THREE.WebGLTextures: sRGB encoded textures have to use RGBAFormat and UnsignedByteType."):console.error("THREE.WebGLTextures: Unsupported texture color space:",z)),_}function vt(A){return typeof HTMLImageElement<"u"&&A instanceof HTMLImageElement?(c.width=A.naturalWidth||A.width,c.height=A.naturalHeight||A.height):typeof VideoFrame<"u"&&A instanceof VideoFrame?(c.width=A.displayWidth,c.height=A.displayHeight):(c.width=A.width,c.height=A.height),c}this.allocateTextureUnit=F,this.resetTextureUnits=D,this.setTexture2D=k,this.setTexture2DArray=W,this.setTexture3D=X,this.setTextureCube=H,this.rebindTextures=xt,this.setupRenderTarget=I,this.updateRenderTargetMipmap=ot,this.updateMultisampleRenderTarget=ye,this.setupDepthRenderbuffer=ze,this.setupFrameBufferTexture=pe,this.useMultisampledRTT=ve}function G0(i,e){function t(n,r=qn){let s,a=$e.getTransfer(r);if(n===Mn)return i.UNSIGNED_BYTE;if(n===Wa)return i.UNSIGNED_SHORT_4_4_4_4;if(n===Xa)return i.UNSIGNED_SHORT_5_5_5_1;if(n===Ul)return i.UNSIGNED_INT_5_9_9_9_REV;if(n===Ol)return i.UNSIGNED_INT_10F_11F_11F_REV;if(n===Ll)return i.BYTE;if(n===Fl)return i.SHORT;if(n===gr)return i.UNSIGNED_SHORT;if(n===Ga)return i.INT;if(n===hi)return i.UNSIGNED_INT;if(n===Pn)return i.FLOAT;if(n===xr)return i.HALF_FLOAT;if(n===Bl)return i.ALPHA;if(n===zl)return i.RGB;if(n===un)return i.RGBA;if(n===or)return i.DEPTH_COMPONENT;if(n===yr)return i.DEPTH_STENCIL;if(n===kl)return i.RED;if(n===$a)return i.RED_INTEGER;if(n===Hl)return i.RG;if(n===qa)return i.RG_INTEGER;if(n===Ya)return i.RGBA_INTEGER;if(n===ps||n===ms||n===gs||n===xs)if(a===Ke)if(s=e.get("WEBGL_compressed_texture_s3tc_srgb"),s!==null){if(n===ps)return s.COMPRESSED_SRGB_S3TC_DXT1_EXT;if(n===ms)return s.COMPRESSED_SRGB_ALPHA_S3TC_DXT1_EXT;if(n===gs)return s.COMPRESSED_SRGB_ALPHA_S3TC_DXT3_EXT;if(n===xs)return s.COMPRESSED_SRGB_ALPHA_S3TC_DXT5_EXT}else return null;else if(s=e.get("WEBGL_compressed_texture_s3tc"),s!==null){if(n===ps)return s.COMPRESSED_RGB_S3TC_DXT1_EXT;if(n===ms)return s.COMPRESSED_RGBA_S3TC_DXT1_EXT;if(n===gs)return s.COMPRESSED_RGBA_S3TC_DXT3_EXT;if(n===xs)return s.COMPRESSED_RGBA_S3TC_DXT5_EXT}else return null;if(n===Za||n===Ja||n===Ka||n===ja)if(s=e.get("WEBGL_compressed_texture_pvrtc"),s!==null){if(n===Za)return s.COMPRESSED_RGB_PVRTC_4BPPV1_IMG;if(n===Ja)return s.COMPRESSED_RGB_PVRTC_2BPPV1_IMG;if(n===Ka)return s.COMPRESSED_RGBA_PVRTC_4BPPV1_IMG;if(n===ja)return s.COMPRESSED_RGBA_PVRTC_2BPPV1_IMG}else return null;if(n===Qa||n===eo||n===to)if(s=e.get("WEBGL_compressed_texture_etc"),s!==null){if(n===Qa||n===eo)return a===Ke?s.COMPRESSED_SRGB8_ETC2:s.COMPRESSED_RGB8_ETC2;if(n===to)return a===Ke?s.COMPRESSED_SRGB8_ALPHA8_ETC2_EAC:s.COMPRESSED_RGBA8_ETC2_EAC}else return null;if(n===no||n===io||n===ro||n===so||n===ao||n===oo||n===lo||n===co||n===uo||n===ho||n===fo||n===po||n===mo||n===go)if(s=e.get("WEBGL_compressed_texture_astc"),s!==null){if(n===no)return a===Ke?s.COMPRESSED_SRGB8_ALPHA8_ASTC_4x4_KHR:s.COMPRESSED_RGBA_ASTC_4x4_KHR;if(n===io)return a===Ke?s.COMPRESSED_SRGB8_ALPHA8_ASTC_5x4_KHR:s.COMPRESSED_RGBA_ASTC_5x4_KHR;if(n===ro)return a===Ke?s.COMPRESSED_SRGB8_ALPHA8_ASTC_5x5_KHR:s.COMPRESSED_RGBA_ASTC_5x5_KHR;if(n===so)return a===Ke?s.COMPRESSED_SRGB8_ALPHA8_ASTC_6x5_KHR:s.COMPRESSED_RGBA_ASTC_6x5_KHR;if(n===ao)return a===Ke?s.COMPRESSED_SRGB8_ALPHA8_ASTC_6x6_KHR:s.COMPRESSED_RGBA_ASTC_6x6_KHR;if(n===oo)return a===Ke?s.COMPRESSED_SRGB8_ALPHA8_ASTC_8x5_KHR:s.COMPRESSED_RGBA_ASTC_8x5_KHR;if(n===lo)return a===Ke?s.COMPRESSED_SRGB8_ALPHA8_ASTC_8x6_KHR:s.COMPRESSED_RGBA_ASTC_8x6_KHR;if(n===co)return a===Ke?s.COMPRESSED_SRGB8_ALPHA8_ASTC_8x8_KHR:s.COMPRESSED_RGBA_ASTC_8x8_KHR;if(n===uo)return a===Ke?s.COMPRESSED_SRGB8_ALPHA8_ASTC_10x5_KHR:s.COMPRESSED_RGBA_ASTC_10x5_KHR;if(n===ho)return a===Ke?s.COMPRESSED_SRGB8_ALPHA8_ASTC_10x6_KHR:s.COMPRESSED_RGBA_ASTC_10x6_KHR;if(n===fo)return a===Ke?s.COMPRESSED_SRGB8_ALPHA8_ASTC_10x8_KHR:s.COMPRESSED_RGBA_ASTC_10x8_KHR;if(n===po)return a===Ke?s.COMPRESSED_SRGB8_ALPHA8_ASTC_10x10_KHR:s.COMPRESSED_RGBA_ASTC_10x10_KHR;if(n===mo)return a===Ke?s.COMPRESSED_SRGB8_ALPHA8_ASTC_12x10_KHR:s.COMPRESSED_RGBA_ASTC_12x10_KHR;if(n===go)return a===Ke?s.COMPRESSED_SRGB8_ALPHA8_ASTC_12x12_KHR:s.COMPRESSED_RGBA_ASTC_12x12_KHR}else return null;if(n===xo||n===_o||n===yo)if(s=e.get("EXT_texture_compression_bptc"),s!==null){if(n===xo)return a===Ke?s.COMPRESSED_SRGB_ALPHA_BPTC_UNORM_EXT:s.COMPRESSED_RGBA_BPTC_UNORM_EXT;if(n===_o)return s.COMPRESSED_RGB_BPTC_SIGNED_FLOAT_EXT;if(n===yo)return s.COMPRESSED_RGB_BPTC_UNSIGNED_FLOAT_EXT}else return null;if(n===vo||n===bo||n===wo||n===Mo)if(s=e.get("EXT_texture_compression_rgtc"),s!==null){if(n===vo)return s.COMPRESSED_RED_RGTC1_EXT;if(n===bo)return s.COMPRESSED_SIGNED_RED_RGTC1_EXT;if(n===wo)return s.COMPRESSED_RED_GREEN_RGTC2_EXT;if(n===Mo)return s.COMPRESSED_SIGNED_RED_GREEN_RGTC2_EXT}else return null;return n===_r?i.UNSIGNED_INT_24_8:i[n]!==void 0?i[n]:null}return{convert:t}}var W0=`
void main() {

	gl_Position = vec4( position, 1.0 );

}`,X0=`
uniform sampler2DArray depthColor;
uniform float depthWidth;
uniform float depthHeight;

void main() {

	vec2 coord = vec2( gl_FragCoord.x / depthWidth, gl_FragCoord.y / depthHeight );

	if ( coord.x >= 1.0 ) {

		gl_FragDepth = texture( depthColor, vec3( coord.x - 1.0, coord.y, 1 ) ).r;

	} else {

		gl_FragDepth = texture( depthColor, vec3( coord.x, coord.y, 0 ) ).r;

	}

}`,cc=class{constructor(){this.texture=null,this.mesh=null,this.depthNear=0,this.depthFar=0}init(e,t){if(this.texture===null){let n=new ts(e.texture);(e.depthNear!==t.depthNear||e.depthFar!==t.depthFar)&&(this.depthNear=e.depthNear,this.depthFar=e.depthFar),this.texture=n}}getMesh(e){if(this.texture!==null&&this.mesh===null){let t=e.cameras[0].viewport,n=new tn({vertexShader:W0,fragmentShader:X0,uniforms:{depthColor:{value:this.texture},depthWidth:{value:t.z},depthHeight:{value:t.w}}});this.mesh=new st(new Ei(20,20),n)}return this.mesh}reset(){this.texture=null,this.mesh=null}getDepthTexture(){return this.texture}},dc=class extends Gn{constructor(e,t){super();let n=this,r=null,s=1,a=null,o="local-floor",l=1,c=null,d=null,u=null,h=null,p=null,g=null,x=typeof XRWebGLBinding<"u",m=new cc,f={},S=t.getContextAttributes(),M=null,y=null,C=[],E=[],R=new He,P=null,w=new Dt;w.viewport=new pt;let v=new Dt;v.viewport=new pt;let T=[w,v],D=new Na,F=null,B=null;this.cameraAutoUpdate=!0,this.enabled=!1,this.isPresenting=!1,this.getController=function(Y){let J=C[Y];return J===void 0&&(J=new hr,C[Y]=J),J.getTargetRaySpace()},this.getControllerGrip=function(Y){let J=C[Y];return J===void 0&&(J=new hr,C[Y]=J),J.getGripSpace()},this.getHand=function(Y){let J=C[Y];return J===void 0&&(J=new hr,C[Y]=J),J.getHandSpace()};function k(Y){let J=E.indexOf(Y.inputSource);if(J===-1)return;let pe=C[J];pe!==void 0&&(pe.update(Y.inputSource,Y.frame,c||a),pe.dispatchEvent({type:Y.type,data:Y.inputSource}))}function W(){r.removeEventListener("select",k),r.removeEventListener("selectstart",k),r.removeEventListener("selectend",k),r.removeEventListener("squeeze",k),r.removeEventListener("squeezestart",k),r.removeEventListener("squeezeend",k),r.removeEventListener("end",W),r.removeEventListener("inputsourceschange",X);for(let Y=0;Y<C.length;Y++){let J=E[Y];J!==null&&(E[Y]=null,C[Y].disconnect(J))}F=null,B=null,m.reset();for(let Y in f)delete f[Y];e.setRenderTarget(M),p=null,h=null,u=null,r=null,y=null,Fe.stop(),n.isPresenting=!1,e.setPixelRatio(P),e.setSize(R.width,R.height,!1),n.dispatchEvent({type:"sessionend"})}this.setFramebufferScaleFactor=function(Y){s=Y,n.isPresenting===!0&&console.warn("THREE.WebXRManager: Cannot change framebuffer scale while presenting.")},this.setReferenceSpaceType=function(Y){o=Y,n.isPresenting===!0&&console.warn("THREE.WebXRManager: Cannot change reference space type while presenting.")},this.getReferenceSpace=function(){return c||a},this.setReferenceSpace=function(Y){c=Y},this.getBaseLayer=function(){return h!==null?h:p},this.getBinding=function(){return u===null&&x&&(u=new XRWebGLBinding(r,t)),u},this.getFrame=function(){return g},this.getSession=function(){return r},this.setSession=async function(Y){if(r=Y,r!==null){if(M=e.getRenderTarget(),r.addEventListener("select",k),r.addEventListener("selectstart",k),r.addEventListener("selectend",k),r.addEventListener("squeeze",k),r.addEventListener("squeezestart",k),r.addEventListener("squeezeend",k),r.addEventListener("end",W),r.addEventListener("inputsourceschange",X),S.xrCompatible!==!0&&await t.makeXRCompatible(),P=e.getPixelRatio(),e.getSize(R),x&&"createProjectionLayer"in XRWebGLBinding.prototype){let pe=null,Ce=null,ge=null;S.depth&&(ge=S.stencil?t.DEPTH24_STENCIL8:t.DEPTH_COMPONENT24,pe=S.stencil?yr:or,Ce=S.stencil?_r:hi);let ze={colorFormat:t.RGBA8,depthFormat:ge,scaleFactor:s};u=this.getBinding(),h=u.createProjectionLayer(ze),r.updateRenderState({layers:[h]}),e.setPixelRatio(1),e.setSize(h.textureWidth,h.textureHeight,!1),y=new Cn(h.textureWidth,h.textureHeight,{format:un,type:Mn,depthTexture:new es(h.textureWidth,h.textureHeight,Ce,void 0,void 0,void 0,void 0,void 0,void 0,pe),stencilBuffer:S.stencil,colorSpace:e.outputColorSpace,samples:S.antialias?4:0,resolveDepthBuffer:h.ignoreDepthValues===!1,resolveStencilBuffer:h.ignoreDepthValues===!1})}else{let pe={antialias:S.antialias,alpha:!0,depth:S.depth,stencil:S.stencil,framebufferScaleFactor:s};p=new XRWebGLLayer(r,t,pe),r.updateRenderState({baseLayer:p}),e.setPixelRatio(1),e.setSize(p.framebufferWidth,p.framebufferHeight,!1),y=new Cn(p.framebufferWidth,p.framebufferHeight,{format:un,type:Mn,colorSpace:e.outputColorSpace,stencilBuffer:S.stencil,resolveDepthBuffer:p.ignoreDepthValues===!1,resolveStencilBuffer:p.ignoreDepthValues===!1})}y.isXRRenderTarget=!0,this.setFoveation(l),c=null,a=await r.requestReferenceSpace(o),Fe.setContext(r),Fe.start(),n.isPresenting=!0,n.dispatchEvent({type:"sessionstart"})}},this.getEnvironmentBlendMode=function(){if(r!==null)return r.environmentBlendMode},this.getDepthTexture=function(){return m.getDepthTexture()};function X(Y){for(let J=0;J<Y.removed.length;J++){let pe=Y.removed[J],Ce=E.indexOf(pe);Ce>=0&&(E[Ce]=null,C[Ce].disconnect(pe))}for(let J=0;J<Y.added.length;J++){let pe=Y.added[J],Ce=E.indexOf(pe);if(Ce===-1){for(let ze=0;ze<C.length;ze++)if(ze>=E.length){E.push(pe),Ce=ze;break}else if(E[ze]===null){E[ze]=pe,Ce=ze;break}if(Ce===-1)break}let ge=C[Ce];ge&&ge.connect(pe)}}let H=new N,Q=new N;function ne(Y,J,pe){H.setFromMatrixPosition(J.matrixWorld),Q.setFromMatrixPosition(pe.matrixWorld);let Ce=H.distanceTo(Q),ge=J.projectionMatrix.elements,ze=pe.projectionMatrix.elements,xt=ge[14]/(ge[10]-1),I=ge[14]/(ge[10]+1),ot=(ge[9]+1)/ge[5],Ue=(ge[9]-1)/ge[5],Ie=(ge[8]-1)/ge[0],ye=(ze[8]+1)/ze[0],lt=xt*Ie,ve=xt*ye,ke=Ce/(-Ie+ye),At=ke*-Ie;if(J.matrixWorld.decompose(Y.position,Y.quaternion,Y.scale),Y.translateX(At),Y.translateZ(ke),Y.matrixWorld.compose(Y.position,Y.quaternion,Y.scale),Y.matrixWorldInverse.copy(Y.matrixWorld).invert(),ge[10]===-1)Y.projectionMatrix.copy(J.projectionMatrix),Y.projectionMatrixInverse.copy(J.projectionMatrixInverse);else{let vt=xt+ke,A=I+ke,_=lt-At,z=ve+(Ce-At),q=ot*I/A*vt,K=Ue*I/A*vt;Y.projectionMatrix.makePerspective(_,z,q,K,vt,A),Y.projectionMatrixInverse.copy(Y.projectionMatrix).invert()}}function fe(Y,J){J===null?Y.matrixWorld.copy(Y.matrix):Y.matrixWorld.multiplyMatrices(J.matrixWorld,Y.matrix),Y.matrixWorldInverse.copy(Y.matrixWorld).invert()}this.updateCamera=function(Y){if(r===null)return;let J=Y.near,pe=Y.far;m.texture!==null&&(m.depthNear>0&&(J=m.depthNear),m.depthFar>0&&(pe=m.depthFar)),D.near=v.near=w.near=J,D.far=v.far=w.far=pe,(F!==D.near||B!==D.far)&&(r.updateRenderState({depthNear:D.near,depthFar:D.far}),F=D.near,B=D.far),D.layers.mask=Y.layers.mask|6,w.layers.mask=D.layers.mask&3,v.layers.mask=D.layers.mask&5;let Ce=Y.parent,ge=D.cameras;fe(D,Ce);for(let ze=0;ze<ge.length;ze++)fe(ge[ze],Ce);ge.length===2?ne(D,w,v):D.projectionMatrix.copy(w.projectionMatrix),De(Y,D,Ce)};function De(Y,J,pe){pe===null?Y.matrix.copy(J.matrixWorld):(Y.matrix.copy(pe.matrixWorld),Y.matrix.invert(),Y.matrix.multiply(J.matrixWorld)),Y.matrix.decompose(Y.position,Y.quaternion,Y.scale),Y.updateMatrixWorld(!0),Y.projectionMatrix.copy(J.projectionMatrix),Y.projectionMatrixInverse.copy(J.projectionMatrixInverse),Y.isPerspectiveCamera&&(Y.fov=lr*2*Math.atan(1/Y.projectionMatrix.elements[5]),Y.zoom=1)}this.getCamera=function(){return D},this.getFoveation=function(){if(!(h===null&&p===null))return l},this.setFoveation=function(Y){l=Y,h!==null&&(h.fixedFoveation=Y),p!==null&&p.fixedFoveation!==void 0&&(p.fixedFoveation=Y)},this.hasDepthSensing=function(){return m.texture!==null},this.getDepthSensingMesh=function(){return m.getMesh(D)},this.getCameraTexture=function(Y){return f[Y]};let Xe=null;function Ze(Y,J){if(d=J.getViewerPose(c||a),g=J,d!==null){let pe=d.views;p!==null&&(e.setRenderTargetFramebuffer(y,p.framebuffer),e.setRenderTarget(y));let Ce=!1;pe.length!==D.cameras.length&&(D.cameras.length=0,Ce=!0);for(let I=0;I<pe.length;I++){let ot=pe[I],Ue=null;if(p!==null)Ue=p.getViewport(ot);else{let ye=u.getViewSubImage(h,ot);Ue=ye.viewport,I===0&&(e.setRenderTargetTextures(y,ye.colorTexture,ye.depthStencilTexture),e.setRenderTarget(y))}let Ie=T[I];Ie===void 0&&(Ie=new Dt,Ie.layers.enable(I),Ie.viewport=new pt,T[I]=Ie),Ie.matrix.fromArray(ot.transform.matrix),Ie.matrix.decompose(Ie.position,Ie.quaternion,Ie.scale),Ie.projectionMatrix.fromArray(ot.projectionMatrix),Ie.projectionMatrixInverse.copy(Ie.projectionMatrix).invert(),Ie.viewport.set(Ue.x,Ue.y,Ue.width,Ue.height),I===0&&(D.matrix.copy(Ie.matrix),D.matrix.decompose(D.position,D.quaternion,D.scale)),Ce===!0&&D.cameras.push(Ie)}let ge=r.enabledFeatures;if(ge&&ge.includes("depth-sensing")&&r.depthUsage=="gpu-optimized"&&x){u=n.getBinding();let I=u.getDepthInformation(pe[0]);I&&I.isValid&&I.texture&&m.init(I,r.renderState)}if(ge&&ge.includes("camera-access")&&x){e.state.unbindTexture(),u=n.getBinding();for(let I=0;I<pe.length;I++){let ot=pe[I].camera;if(ot){let Ue=f[ot];Ue||(Ue=new ts,f[ot]=Ue);let Ie=u.getCameraImage(ot);Ue.sourceTexture=Ie}}}}for(let pe=0;pe<C.length;pe++){let Ce=E[pe],ge=C[pe];Ce!==null&&ge!==void 0&&ge.update(Ce,J,c||a)}Xe&&Xe(Y,J),J.detectedPlanes&&n.dispatchEvent({type:"planesdetected",data:J}),g=null}let Fe=new Ru;Fe.setAnimationLoop(Ze),this.setAnimationLoop=function(Y){Xe=Y},this.dispose=function(){}}},Pi=new en,$0=new ct;function q0(i,e){function t(m,f){m.matrixAutoUpdate===!0&&m.updateMatrix(),f.value.copy(m.matrix)}function n(m,f){f.color.getRGB(m.fogColor.value,ql(i)),f.isFog?(m.fogNear.value=f.near,m.fogFar.value=f.far):f.isFogExp2&&(m.fogDensity.value=f.density)}function r(m,f,S,M,y){f.isMeshBasicMaterial||f.isMeshLambertMaterial?s(m,f):f.isMeshToonMaterial?(s(m,f),u(m,f)):f.isMeshPhongMaterial?(s(m,f),d(m,f)):f.isMeshStandardMaterial?(s(m,f),h(m,f),f.isMeshPhysicalMaterial&&p(m,f,y)):f.isMeshMatcapMaterial?(s(m,f),g(m,f)):f.isMeshDepthMaterial?s(m,f):f.isMeshDistanceMaterial?(s(m,f),x(m,f)):f.isMeshNormalMaterial?s(m,f):f.isLineBasicMaterial?(a(m,f),f.isLineDashedMaterial&&o(m,f)):f.isPointsMaterial?l(m,f,S,M):f.isSpriteMaterial?c(m,f):f.isShadowMaterial?(m.color.value.copy(f.color),m.opacity.value=f.opacity):f.isShaderMaterial&&(f.uniformsNeedUpdate=!1)}function s(m,f){m.opacity.value=f.opacity,f.color&&m.diffuse.value.copy(f.color),f.emissive&&m.emissive.value.copy(f.emissive).multiplyScalar(f.emissiveIntensity),f.map&&(m.map.value=f.map,t(f.map,m.mapTransform)),f.alphaMap&&(m.alphaMap.value=f.alphaMap,t(f.alphaMap,m.alphaMapTransform)),f.bumpMap&&(m.bumpMap.value=f.bumpMap,t(f.bumpMap,m.bumpMapTransform),m.bumpScale.value=f.bumpScale,f.side===zt&&(m.bumpScale.value*=-1)),f.normalMap&&(m.normalMap.value=f.normalMap,t(f.normalMap,m.normalMapTransform),m.normalScale.value.copy(f.normalScale),f.side===zt&&m.normalScale.value.negate()),f.displacementMap&&(m.displacementMap.value=f.displacementMap,t(f.displacementMap,m.displacementMapTransform),m.displacementScale.value=f.displacementScale,m.displacementBias.value=f.displacementBias),f.emissiveMap&&(m.emissiveMap.value=f.emissiveMap,t(f.emissiveMap,m.emissiveMapTransform)),f.specularMap&&(m.specularMap.value=f.specularMap,t(f.specularMap,m.specularMapTransform)),f.alphaTest>0&&(m.alphaTest.value=f.alphaTest);let S=e.get(f),M=S.envMap,y=S.envMapRotation;M&&(m.envMap.value=M,Pi.copy(y),Pi.x*=-1,Pi.y*=-1,Pi.z*=-1,M.isCubeTexture&&M.isRenderTargetTexture===!1&&(Pi.y*=-1,Pi.z*=-1),m.envMapRotation.value.setFromMatrix4($0.makeRotationFromEuler(Pi)),m.flipEnvMap.value=M.isCubeTexture&&M.isRenderTargetTexture===!1?-1:1,m.reflectivity.value=f.reflectivity,m.ior.value=f.ior,m.refractionRatio.value=f.refractionRatio),f.lightMap&&(m.lightMap.value=f.lightMap,m.lightMapIntensity.value=f.lightMapIntensity,t(f.lightMap,m.lightMapTransform)),f.aoMap&&(m.aoMap.value=f.aoMap,m.aoMapIntensity.value=f.aoMapIntensity,t(f.aoMap,m.aoMapTransform))}function a(m,f){m.diffuse.value.copy(f.color),m.opacity.value=f.opacity,f.map&&(m.map.value=f.map,t(f.map,m.mapTransform))}function o(m,f){m.dashSize.value=f.dashSize,m.totalSize.value=f.dashSize+f.gapSize,m.scale.value=f.scale}function l(m,f,S,M){m.diffuse.value.copy(f.color),m.opacity.value=f.opacity,m.size.value=f.size*S,m.scale.value=M*.5,f.map&&(m.map.value=f.map,t(f.map,m.uvTransform)),f.alphaMap&&(m.alphaMap.value=f.alphaMap,t(f.alphaMap,m.alphaMapTransform)),f.alphaTest>0&&(m.alphaTest.value=f.alphaTest)}function c(m,f){m.diffuse.value.copy(f.color),m.opacity.value=f.opacity,m.rotation.value=f.rotation,f.map&&(m.map.value=f.map,t(f.map,m.mapTransform)),f.alphaMap&&(m.alphaMap.value=f.alphaMap,t(f.alphaMap,m.alphaMapTransform)),f.alphaTest>0&&(m.alphaTest.value=f.alphaTest)}function d(m,f){m.specular.value.copy(f.specular),m.shininess.value=Math.max(f.shininess,1e-4)}function u(m,f){f.gradientMap&&(m.gradientMap.value=f.gradientMap)}function h(m,f){m.metalness.value=f.metalness,f.metalnessMap&&(m.metalnessMap.value=f.metalnessMap,t(f.metalnessMap,m.metalnessMapTransform)),m.roughness.value=f.roughness,f.roughnessMap&&(m.roughnessMap.value=f.roughnessMap,t(f.roughnessMap,m.roughnessMapTransform)),f.envMap&&(m.envMapIntensity.value=f.envMapIntensity)}function p(m,f,S){m.ior.value=f.ior,f.sheen>0&&(m.sheenColor.value.copy(f.sheenColor).multiplyScalar(f.sheen),m.sheenRoughness.value=f.sheenRoughness,f.sheenColorMap&&(m.sheenColorMap.value=f.sheenColorMap,t(f.sheenColorMap,m.sheenColorMapTransform)),f.sheenRoughnessMap&&(m.sheenRoughnessMap.value=f.sheenRoughnessMap,t(f.sheenRoughnessMap,m.sheenRoughnessMapTransform))),f.clearcoat>0&&(m.clearcoat.value=f.clearcoat,m.clearcoatRoughness.value=f.clearcoatRoughness,f.clearcoatMap&&(m.clearcoatMap.value=f.clearcoatMap,t(f.clearcoatMap,m.clearcoatMapTransform)),f.clearcoatRoughnessMap&&(m.clearcoatRoughnessMap.value=f.clearcoatRoughnessMap,t(f.clearcoatRoughnessMap,m.clearcoatRoughnessMapTransform)),f.clearcoatNormalMap&&(m.clearcoatNormalMap.value=f.clearcoatNormalMap,t(f.clearcoatNormalMap,m.clearcoatNormalMapTransform),m.clearcoatNormalScale.value.copy(f.clearcoatNormalScale),f.side===zt&&m.clearcoatNormalScale.value.negate())),f.dispersion>0&&(m.dispersion.value=f.dispersion),f.iridescence>0&&(m.iridescence.value=f.iridescence,m.iridescenceIOR.value=f.iridescenceIOR,m.iridescenceThicknessMinimum.value=f.iridescenceThicknessRange[0],m.iridescenceThicknessMaximum.value=f.iridescenceThicknessRange[1],f.iridescenceMap&&(m.iridescenceMap.value=f.iridescenceMap,t(f.iridescenceMap,m.iridescenceMapTransform)),f.iridescenceThicknessMap&&(m.iridescenceThicknessMap.value=f.iridescenceThicknessMap,t(f.iridescenceThicknessMap,m.iridescenceThicknessMapTransform))),f.transmission>0&&(m.transmission.value=f.transmission,m.transmissionSamplerMap.value=S.texture,m.transmissionSamplerSize.value.set(S.width,S.height),f.transmissionMap&&(m.transmissionMap.value=f.transmissionMap,t(f.transmissionMap,m.transmissionMapTransform)),m.thickness.value=f.thickness,f.thicknessMap&&(m.thicknessMap.value=f.thicknessMap,t(f.thicknessMap,m.thicknessMapTransform)),m.attenuationDistance.value=f.attenuationDistance,m.attenuationColor.value.copy(f.attenuationColor)),f.anisotropy>0&&(m.anisotropyVector.value.set(f.anisotropy*Math.cos(f.anisotropyRotation),f.anisotropy*Math.sin(f.anisotropyRotation)),f.anisotropyMap&&(m.anisotropyMap.value=f.anisotropyMap,t(f.anisotropyMap,m.anisotropyMapTransform))),m.specularIntensity.value=f.specularIntensity,m.specularColor.value.copy(f.specularColor),f.specularColorMap&&(m.specularColorMap.value=f.specularColorMap,t(f.specularColorMap,m.specularColorMapTransform)),f.specularIntensityMap&&(m.specularIntensityMap.value=f.specularIntensityMap,t(f.specularIntensityMap,m.specularIntensityMapTransform))}function g(m,f){f.matcap&&(m.matcap.value=f.matcap)}function x(m,f){let S=e.get(f).light;m.referencePosition.value.setFromMatrixPosition(S.matrixWorld),m.nearDistance.value=S.shadow.camera.near,m.farDistance.value=S.shadow.camera.far}return{refreshFogUniforms:n,refreshMaterialUniforms:r}}function Y0(i,e,t,n){let r={},s={},a=[],o=i.getParameter(i.MAX_UNIFORM_BUFFER_BINDINGS);function l(S,M){let y=M.program;n.uniformBlockBinding(S,y)}function c(S,M){let y=r[S.id];y===void 0&&(g(S),y=d(S),r[S.id]=y,S.addEventListener("dispose",m));let C=M.program;n.updateUBOMapping(S,C);let E=e.render.frame;s[S.id]!==E&&(h(S),s[S.id]=E)}function d(S){let M=u();S.__bindingPointIndex=M;let y=i.createBuffer(),C=S.__size,E=S.usage;return i.bindBuffer(i.UNIFORM_BUFFER,y),i.bufferData(i.UNIFORM_BUFFER,C,E),i.bindBuffer(i.UNIFORM_BUFFER,null),i.bindBufferBase(i.UNIFORM_BUFFER,M,y),y}function u(){for(let S=0;S<o;S++)if(a.indexOf(S)===-1)return a.push(S),S;return console.error("THREE.WebGLRenderer: Maximum number of simultaneously usable uniforms groups reached."),0}function h(S){let M=r[S.id],y=S.uniforms,C=S.__cache;i.bindBuffer(i.UNIFORM_BUFFER,M);for(let E=0,R=y.length;E<R;E++){let P=Array.isArray(y[E])?y[E]:[y[E]];for(let w=0,v=P.length;w<v;w++){let T=P[w];if(p(T,E,w,C)===!0){let D=T.__offset,F=Array.isArray(T.value)?T.value:[T.value],B=0;for(let k=0;k<F.length;k++){let W=F[k],X=x(W);typeof W=="number"||typeof W=="boolean"?(T.__data[0]=W,i.bufferSubData(i.UNIFORM_BUFFER,D+B,T.__data)):W.isMatrix3?(T.__data[0]=W.elements[0],T.__data[1]=W.elements[1],T.__data[2]=W.elements[2],T.__data[3]=0,T.__data[4]=W.elements[3],T.__data[5]=W.elements[4],T.__data[6]=W.elements[5],T.__data[7]=0,T.__data[8]=W.elements[6],T.__data[9]=W.elements[7],T.__data[10]=W.elements[8],T.__data[11]=0):(W.toArray(T.__data,B),B+=X.storage/Float32Array.BYTES_PER_ELEMENT)}i.bufferSubData(i.UNIFORM_BUFFER,D,T.__data)}}}i.bindBuffer(i.UNIFORM_BUFFER,null)}function p(S,M,y,C){let E=S.value,R=M+"_"+y;if(C[R]===void 0)return typeof E=="number"||typeof E=="boolean"?C[R]=E:C[R]=E.clone(),!0;{let P=C[R];if(typeof E=="number"||typeof E=="boolean"){if(P!==E)return C[R]=E,!0}else if(P.equals(E)===!1)return P.copy(E),!0}return!1}function g(S){let M=S.uniforms,y=0,C=16;for(let R=0,P=M.length;R<P;R++){let w=Array.isArray(M[R])?M[R]:[M[R]];for(let v=0,T=w.length;v<T;v++){let D=w[v],F=Array.isArray(D.value)?D.value:[D.value];for(let B=0,k=F.length;B<k;B++){let W=F[B],X=x(W),H=y%C,Q=H%X.boundary,ne=H+Q;y+=Q,ne!==0&&C-ne<X.storage&&(y+=C-ne),D.__data=new Float32Array(X.storage/Float32Array.BYTES_PER_ELEMENT),D.__offset=y,y+=X.storage}}}let E=y%C;return E>0&&(y+=C-E),S.__size=y,S.__cache={},this}function x(S){let M={boundary:0,storage:0};return typeof S=="number"||typeof S=="boolean"?(M.boundary=4,M.storage=4):S.isVector2?(M.boundary=8,M.storage=8):S.isVector3||S.isColor?(M.boundary=16,M.storage=12):S.isVector4?(M.boundary=16,M.storage=16):S.isMatrix3?(M.boundary=48,M.storage=48):S.isMatrix4?(M.boundary=64,M.storage=64):S.isTexture?console.warn("THREE.WebGLRenderer: Texture samplers can not be part of an uniforms group."):console.warn("THREE.WebGLRenderer: Unsupported uniform value type.",S),M}function m(S){let M=S.target;M.removeEventListener("dispose",m);let y=a.indexOf(M.__bindingPointIndex);a.splice(y,1),i.deleteBuffer(r[M.id]),delete r[M.id],delete s[M.id]}function f(){for(let S in r)i.deleteBuffer(r[S]);a=[],r={},s={}}return{bind:l,update:c,dispose:f}}var Co=class{constructor(e={}){let{canvas:t=eu(),context:n=null,depth:r=!0,stencil:s=!1,alpha:a=!1,antialias:o=!1,premultipliedAlpha:l=!0,preserveDrawingBuffer:c=!1,powerPreference:d="default",failIfMajorPerformanceCaveat:u=!1,reversedDepthBuffer:h=!1}=e;this.isWebGLRenderer=!0;let p;if(n!==null){if(typeof WebGLRenderingContext<"u"&&n instanceof WebGLRenderingContext)throw new Error("THREE.WebGLRenderer: WebGL 1 is not supported since r163.");p=n.getContextAttributes().alpha}else p=a;let g=new Uint32Array(4),x=new Int32Array(4),m=null,f=null,S=[],M=[];this.domElement=t,this.debug={checkShaderErrors:!0,onShaderError:null},this.autoClear=!0,this.autoClearColor=!0,this.autoClearDepth=!0,this.autoClearStencil=!0,this.sortObjects=!0,this.clippingPlanes=[],this.localClippingEnabled=!1,this.toneMapping=$n,this.toneMappingExposure=1,this.transmissionResolutionScale=1;let y=this,C=!1;this._outputColorSpace=Nt;let E=0,R=0,P=null,w=-1,v=null,T=new pt,D=new pt,F=null,B=new Ne(0),k=0,W=t.width,X=t.height,H=1,Q=null,ne=null,fe=new pt(0,0,W,X),De=new pt(0,0,W,X),Xe=!1,Ze=new pr,Fe=!1,Y=!1,J=new ct,pe=new N,Ce=new pt,ge={background:null,fog:null,environment:null,overrideMaterial:null,isScene:!0},ze=!1;function xt(){return P===null?H:1}let I=n;function ot(b,U){return t.getContext(b,U)}try{let b={alpha:!0,depth:r,stencil:s,antialias:o,premultipliedAlpha:l,preserveDrawingBuffer:c,powerPreference:d,failIfMajorPerformanceCaveat:u};if("setAttribute"in t&&t.setAttribute("data-engine",`three.js r${"180"}`),t.addEventListener("webglcontextlost",ae,!1),t.addEventListener("webglcontextrestored",me,!1),t.addEventListener("webglcontextcreationerror",ee,!1),I===null){let U="webgl2";if(I=ot(U,b),I===null)throw ot(U)?new Error("Error creating WebGL context with your selected attributes."):new Error("Error creating WebGL context.")}}catch(b){throw console.error("THREE.WebGLRenderer: "+b.message),b}let Ue,Ie,ye,lt,ve,ke,At,vt,A,_,z,q,K,$,Se,se,be,we,ie,de,Re,Me,le,Be;function L(){Ue=new hg(I),Ue.init(),Me=new G0(I,Ue),Ie=new sg(I,Ue,e,Me),ye=new H0(I,Ue),Ie.reversedDepthBuffer&&h&&ye.buffers.depth.setReversed(!0),lt=new mg(I),ve=new C0,ke=new V0(I,Ue,ye,ve,Ie,Me,lt),At=new og(y),vt=new ug(y),A=new bf(I),le=new ig(I,A),_=new fg(I,A,lt,le),z=new xg(I,_,A,lt),ie=new gg(I,Ie,ke),se=new ag(ve),q=new A0(y,At,vt,Ue,Ie,le,se),K=new q0(y,ve),$=new I0,Se=new U0(Ue),we=new ng(y,At,vt,ye,z,p,l),be=new z0(y,z,Ie),Be=new Y0(I,lt,Ie,ye),de=new rg(I,Ue,lt),Re=new pg(I,Ue,lt),lt.programs=q.programs,y.capabilities=Ie,y.extensions=Ue,y.properties=ve,y.renderLists=$,y.shadowMap=be,y.state=ye,y.info=lt}L();let re=new dc(y,I);this.xr=re,this.getContext=function(){return I},this.getContextAttributes=function(){return I.getContextAttributes()},this.forceContextLoss=function(){let b=Ue.get("WEBGL_lose_context");b&&b.loseContext()},this.forceContextRestore=function(){let b=Ue.get("WEBGL_lose_context");b&&b.restoreContext()},this.getPixelRatio=function(){return H},this.setPixelRatio=function(b){b!==void 0&&(H=b,this.setSize(W,X,!1))},this.getSize=function(b){return b.set(W,X)},this.setSize=function(b,U,V=!0){if(re.isPresenting){console.warn("THREE.WebGLRenderer: Can't change size while VR device is presenting.");return}W=b,X=U,t.width=Math.floor(b*H),t.height=Math.floor(U*H),V===!0&&(t.style.width=b+"px",t.style.height=U+"px"),this.setViewport(0,0,b,U)},this.getDrawingBufferSize=function(b){return b.set(W*H,X*H).floor()},this.setDrawingBufferSize=function(b,U,V){W=b,X=U,H=V,t.width=Math.floor(b*V),t.height=Math.floor(U*V),this.setViewport(0,0,b,U)},this.getCurrentViewport=function(b){return b.copy(T)},this.getViewport=function(b){return b.copy(fe)},this.setViewport=function(b,U,V,G){b.isVector4?fe.set(b.x,b.y,b.z,b.w):fe.set(b,U,V,G),ye.viewport(T.copy(fe).multiplyScalar(H).round())},this.getScissor=function(b){return b.copy(De)},this.setScissor=function(b,U,V,G){b.isVector4?De.set(b.x,b.y,b.z,b.w):De.set(b,U,V,G),ye.scissor(D.copy(De).multiplyScalar(H).round())},this.getScissorTest=function(){return Xe},this.setScissorTest=function(b){ye.setScissorTest(Xe=b)},this.setOpaqueSort=function(b){Q=b},this.setTransparentSort=function(b){ne=b},this.getClearColor=function(b){return b.copy(we.getClearColor())},this.setClearColor=function(){we.setClearColor(...arguments)},this.getClearAlpha=function(){return we.getClearAlpha()},this.setClearAlpha=function(){we.setClearAlpha(...arguments)},this.clear=function(b=!0,U=!0,V=!0){let G=0;if(b){let O=!1;if(P!==null){let te=P.texture.format;O=te===Ya||te===qa||te===$a}if(O){let te=P.texture.type,ce=te===Mn||te===hi||te===gr||te===_r||te===Wa||te===Xa,xe=we.getClearColor(),he=we.getClearAlpha(),Ae=xe.r,Pe=xe.g,Ee=xe.b;ce?(g[0]=Ae,g[1]=Pe,g[2]=Ee,g[3]=he,I.clearBufferuiv(I.COLOR,0,g)):(x[0]=Ae,x[1]=Pe,x[2]=Ee,x[3]=he,I.clearBufferiv(I.COLOR,0,x))}else G|=I.COLOR_BUFFER_BIT}U&&(G|=I.DEPTH_BUFFER_BIT),V&&(G|=I.STENCIL_BUFFER_BIT,this.state.buffers.stencil.setMask(4294967295)),I.clear(G)},this.clearColor=function(){this.clear(!0,!1,!1)},this.clearDepth=function(){this.clear(!1,!0,!1)},this.clearStencil=function(){this.clear(!1,!1,!0)},this.dispose=function(){t.removeEventListener("webglcontextlost",ae,!1),t.removeEventListener("webglcontextrestored",me,!1),t.removeEventListener("webglcontextcreationerror",ee,!1),we.dispose(),$.dispose(),Se.dispose(),ve.dispose(),At.dispose(),vt.dispose(),z.dispose(),le.dispose(),Be.dispose(),q.dispose(),re.dispose(),re.removeEventListener("sessionstart",En),re.removeEventListener("sessionend",Nc),mi.stop()};function ae(b){b.preventDefault(),console.log("THREE.WebGLRenderer: Context Lost."),C=!0}function me(){console.log("THREE.WebGLRenderer: Context Restored."),C=!1;let b=lt.autoReset,U=be.enabled,V=be.autoUpdate,G=be.needsUpdate,O=be.type;L(),lt.autoReset=b,be.enabled=U,be.autoUpdate=V,be.needsUpdate=G,be.type=O}function ee(b){console.error("THREE.WebGLRenderer: A WebGL context could not be created. Reason: ",b.statusMessage)}function Z(b){let U=b.target;U.removeEventListener("dispose",Z),_e(U)}function _e(b){Le(b),ve.remove(b)}function Le(b){let U=ve.get(b).programs;U!==void 0&&(U.forEach(function(V){q.releaseProgram(V)}),b.isShaderMaterial&&q.releaseShaderCache(b))}this.renderBufferDirect=function(b,U,V,G,O,te){U===null&&(U=ge);let ce=O.isMesh&&O.matrixWorld.determinant()<0,xe=vh(b,U,V,G,O);ye.setMaterial(G,ce);let he=V.index,Ae=1;if(G.wireframe===!0){if(he=_.getWireframeAttribute(V),he===void 0)return;Ae=2}let Pe=V.drawRange,Ee=V.attributes.position,We=Pe.start*Ae,Qe=(Pe.start+Pe.count)*Ae;te!==null&&(We=Math.max(We,te.start*Ae),Qe=Math.min(Qe,(te.start+te.count)*Ae)),he!==null?(We=Math.max(We,0),Qe=Math.min(Qe,he.count)):Ee!=null&&(We=Math.max(We,0),Qe=Math.min(Qe,Ee.count));let _t=Qe-We;if(_t<0||_t===1/0)return;le.setup(O,G,xe,V,he);let it,et=de;if(he!==null&&(it=A.get(he),et=Re,et.setIndex(it)),O.isMesh)G.wireframe===!0?(ye.setLineWidth(G.wireframeLinewidth*xt()),et.setMode(I.LINES)):et.setMode(I.TRIANGLES);else if(O.isLine){let Te=G.linewidth;Te===void 0&&(Te=1),ye.setLineWidth(Te*xt()),O.isLineSegments?et.setMode(I.LINES):O.isLineLoop?et.setMode(I.LINE_LOOP):et.setMode(I.LINE_STRIP)}else O.isPoints?et.setMode(I.POINTS):O.isSprite&&et.setMode(I.TRIANGLES);if(O.isBatchedMesh)if(O._multiDrawInstances!==null)cr("THREE.WebGLRenderer: renderMultiDrawInstances has been deprecated and will be removed in r184. Append to renderMultiDraw arguments and use indirection."),et.renderMultiDrawInstances(O._multiDrawStarts,O._multiDrawCounts,O._multiDrawCount,O._multiDrawInstances);else if(Ue.get("WEBGL_multi_draw"))et.renderMultiDraw(O._multiDrawStarts,O._multiDrawCounts,O._multiDrawCount);else{let Te=O._multiDrawStarts,ht=O._multiDrawCounts,qe=O._multiDrawCount,Jt=he?A.get(he).bytesPerElement:1,Vi=ve.get(G).currentProgram.getUniforms();for(let Kt=0;Kt<qe;Kt++)Vi.setValue(I,"_gl_DrawID",Kt),et.render(Te[Kt]/Jt,ht[Kt])}else if(O.isInstancedMesh)et.renderInstances(We,_t,O.count);else if(V.isInstancedBufferGeometry){let Te=V._maxInstanceCount!==void 0?V._maxInstanceCount:1/0,ht=Math.min(V.instanceCount,Te);et.renderInstances(We,_t,ht)}else et.render(We,_t)};function nt(b,U,V){b.transparent===!0&&b.side===dn&&b.forceSinglePass===!1?(b.side=zt,b.needsUpdate=!0,Rs(b,U,V),b.side=Vn,b.needsUpdate=!0,Rs(b,U,V),b.side=dn):Rs(b,U,V)}this.compile=function(b,U,V=null){V===null&&(V=b),f=Se.get(V),f.init(U),M.push(f),V.traverseVisible(function(O){O.isLight&&O.layers.test(U.layers)&&(f.pushLight(O),O.castShadow&&f.pushShadow(O))}),b!==V&&b.traverseVisible(function(O){O.isLight&&O.layers.test(U.layers)&&(f.pushLight(O),O.castShadow&&f.pushShadow(O))}),f.setupLights();let G=new Set;return b.traverse(function(O){if(!(O.isMesh||O.isPoints||O.isLine||O.isSprite))return;let te=O.material;if(te)if(Array.isArray(te))for(let ce=0;ce<te.length;ce++){let xe=te[ce];nt(xe,V,O),G.add(xe)}else nt(te,V,O),G.add(te)}),f=M.pop(),G},this.compileAsync=function(b,U,V=null){let G=this.compile(b,U,V);return new Promise(O=>{function te(){if(G.forEach(function(ce){ve.get(ce).currentProgram.isReady()&&G.delete(ce)}),G.size===0){O(b);return}setTimeout(te,10)}Ue.get("KHR_parallel_shader_compile")!==null?te():setTimeout(te,10)})};let Ye=null;function Ln(b){Ye&&Ye(b)}function En(){mi.stop()}function Nc(){mi.start()}let mi=new Ru;mi.setAnimationLoop(Ln),typeof self<"u"&&mi.setContext(self),this.setAnimationLoop=function(b){Ye=b,re.setAnimationLoop(b),b===null?mi.stop():mi.start()},re.addEventListener("sessionstart",En),re.addEventListener("sessionend",Nc),this.render=function(b,U){if(U!==void 0&&U.isCamera!==!0){console.error("THREE.WebGLRenderer.render: camera is not an instance of THREE.Camera.");return}if(C===!0)return;if(b.matrixWorldAutoUpdate===!0&&b.updateMatrixWorld(),U.parent===null&&U.matrixWorldAutoUpdate===!0&&U.updateMatrixWorld(),re.enabled===!0&&re.isPresenting===!0&&(re.cameraAutoUpdate===!0&&re.updateCamera(U),U=re.getCamera()),b.isScene===!0&&b.onBeforeRender(y,b,U,P),f=Se.get(b,M.length),f.init(U),M.push(f),J.multiplyMatrices(U.projectionMatrix,U.matrixWorldInverse),Ze.setFromProjectionMatrix(J,yn,U.reversedDepth),Y=this.localClippingEnabled,Fe=se.init(this.clippingPlanes,Y),m=$.get(b,S.length),m.init(),S.push(m),re.enabled===!0&&re.isPresenting===!0){let te=y.xr.getDepthSensingMesh();te!==null&&Xo(te,U,-1/0,y.sortObjects)}Xo(b,U,0,y.sortObjects),m.finish(),y.sortObjects===!0&&m.sort(Q,ne),ze=re.enabled===!1||re.isPresenting===!1||re.hasDepthSensing()===!1,ze&&we.addToRenderList(m,b),this.info.render.frame++,Fe===!0&&se.beginShadows();let V=f.state.shadowsArray;be.render(V,b,U),Fe===!0&&se.endShadows(),this.info.autoReset===!0&&this.info.reset();let G=m.opaque,O=m.transmissive;if(f.setupLights(),U.isArrayCamera){let te=U.cameras;if(O.length>0)for(let ce=0,xe=te.length;ce<xe;ce++){let he=te[ce];Lc(G,O,b,he)}ze&&we.render(b);for(let ce=0,xe=te.length;ce<xe;ce++){let he=te[ce];Dc(m,b,he,he.viewport)}}else O.length>0&&Lc(G,O,b,U),ze&&we.render(b),Dc(m,b,U);P!==null&&R===0&&(ke.updateMultisampleRenderTarget(P),ke.updateRenderTargetMipmap(P)),b.isScene===!0&&b.onAfterRender(y,b,U),le.resetDefaultState(),w=-1,v=null,M.pop(),M.length>0?(f=M[M.length-1],Fe===!0&&se.setGlobalState(y.clippingPlanes,f.state.camera)):f=null,S.pop(),S.length>0?m=S[S.length-1]:m=null};function Xo(b,U,V,G){if(b.visible===!1)return;if(b.layers.test(U.layers)){if(b.isGroup)V=b.renderOrder;else if(b.isLOD)b.autoUpdate===!0&&b.update(U);else if(b.isLight)f.pushLight(b),b.castShadow&&f.pushShadow(b);else if(b.isSprite){if(!b.frustumCulled||Ze.intersectsSprite(b)){G&&Ce.setFromMatrixPosition(b.matrixWorld).applyMatrix4(J);let ce=z.update(b),xe=b.material;xe.visible&&m.push(b,ce,xe,V,Ce.z,null)}}else if((b.isMesh||b.isLine||b.isPoints)&&(!b.frustumCulled||Ze.intersectsObject(b))){let ce=z.update(b),xe=b.material;if(G&&(b.boundingSphere!==void 0?(b.boundingSphere===null&&b.computeBoundingSphere(),Ce.copy(b.boundingSphere.center)):(ce.boundingSphere===null&&ce.computeBoundingSphere(),Ce.copy(ce.boundingSphere.center)),Ce.applyMatrix4(b.matrixWorld).applyMatrix4(J)),Array.isArray(xe)){let he=ce.groups;for(let Ae=0,Pe=he.length;Ae<Pe;Ae++){let Ee=he[Ae],We=xe[Ee.materialIndex];We&&We.visible&&m.push(b,ce,We,V,Ce.z,Ee)}}else xe.visible&&m.push(b,ce,xe,V,Ce.z,null)}}let te=b.children;for(let ce=0,xe=te.length;ce<xe;ce++)Xo(te[ce],U,V,G)}function Dc(b,U,V,G){let O=b.opaque,te=b.transmissive,ce=b.transparent;f.setupLightsView(V),Fe===!0&&se.setGlobalState(y.clippingPlanes,V),G&&ye.viewport(T.copy(G)),O.length>0&&Cs(O,U,V),te.length>0&&Cs(te,U,V),ce.length>0&&Cs(ce,U,V),ye.buffers.depth.setTest(!0),ye.buffers.depth.setMask(!0),ye.buffers.color.setMask(!0),ye.setPolygonOffset(!1)}function Lc(b,U,V,G){if((V.isScene===!0?V.overrideMaterial:null)!==null)return;f.state.transmissionRenderTarget[G.id]===void 0&&(f.state.transmissionRenderTarget[G.id]=new Cn(1,1,{generateMipmaps:!0,type:Ue.has("EXT_color_buffer_half_float")||Ue.has("EXT_color_buffer_float")?xr:Mn,minFilter:ui,samples:4,stencilBuffer:s,resolveDepthBuffer:!1,resolveStencilBuffer:!1,colorSpace:$e.workingColorSpace}));let te=f.state.transmissionRenderTarget[G.id],ce=G.viewport||T;te.setSize(ce.z*y.transmissionResolutionScale,ce.w*y.transmissionResolutionScale);let xe=y.getRenderTarget(),he=y.getActiveCubeFace(),Ae=y.getActiveMipmapLevel();y.setRenderTarget(te),y.getClearColor(B),k=y.getClearAlpha(),k<1&&y.setClearColor(16777215,.5),y.clear(),ze&&we.render(V);let Pe=y.toneMapping;y.toneMapping=$n;let Ee=G.viewport;if(G.viewport!==void 0&&(G.viewport=void 0),f.setupLightsView(G),Fe===!0&&se.setGlobalState(y.clippingPlanes,G),Cs(b,V,G),ke.updateMultisampleRenderTarget(te),ke.updateRenderTargetMipmap(te),Ue.has("WEBGL_multisampled_render_to_texture")===!1){let We=!1;for(let Qe=0,_t=U.length;Qe<_t;Qe++){let it=U[Qe],et=it.object,Te=it.geometry,ht=it.material,qe=it.group;if(ht.side===dn&&et.layers.test(G.layers)){let Jt=ht.side;ht.side=zt,ht.needsUpdate=!0,Fc(et,V,G,Te,ht,qe),ht.side=Jt,ht.needsUpdate=!0,We=!0}}We===!0&&(ke.updateMultisampleRenderTarget(te),ke.updateRenderTargetMipmap(te))}y.setRenderTarget(xe,he,Ae),y.setClearColor(B,k),Ee!==void 0&&(G.viewport=Ee),y.toneMapping=Pe}function Cs(b,U,V){let G=U.isScene===!0?U.overrideMaterial:null;for(let O=0,te=b.length;O<te;O++){let ce=b[O],xe=ce.object,he=ce.geometry,Ae=ce.group,Pe=ce.material;Pe.allowOverride===!0&&G!==null&&(Pe=G),xe.layers.test(V.layers)&&Fc(xe,U,V,he,Pe,Ae)}}function Fc(b,U,V,G,O,te){b.onBeforeRender(y,U,V,G,O,te),b.modelViewMatrix.multiplyMatrices(V.matrixWorldInverse,b.matrixWorld),b.normalMatrix.getNormalMatrix(b.modelViewMatrix),O.onBeforeRender(y,U,V,G,b,te),O.transparent===!0&&O.side===dn&&O.forceSinglePass===!1?(O.side=zt,O.needsUpdate=!0,y.renderBufferDirect(V,U,G,O,b,te),O.side=Vn,O.needsUpdate=!0,y.renderBufferDirect(V,U,G,O,b,te),O.side=dn):y.renderBufferDirect(V,U,G,O,b,te),b.onAfterRender(y,U,V,G,O,te)}function Rs(b,U,V){U.isScene!==!0&&(U=ge);let G=ve.get(b),O=f.state.lights,te=f.state.shadowsArray,ce=O.state.version,xe=q.getParameters(b,O.state,te,U,V),he=q.getProgramCacheKey(xe),Ae=G.programs;G.environment=b.isMeshStandardMaterial?U.environment:null,G.fog=U.fog,G.envMap=(b.isMeshStandardMaterial?vt:At).get(b.envMap||G.environment),G.envMapRotation=G.environment!==null&&b.envMap===null?U.environmentRotation:b.envMapRotation,Ae===void 0&&(b.addEventListener("dispose",Z),Ae=new Map,G.programs=Ae);let Pe=Ae.get(he);if(Pe!==void 0){if(G.currentProgram===Pe&&G.lightsStateVersion===ce)return Oc(b,xe),Pe}else xe.uniforms=q.getUniforms(b),b.onBeforeCompile(xe,y),Pe=q.acquireProgram(xe,he),Ae.set(he,Pe),G.uniforms=xe.uniforms;let Ee=G.uniforms;return(!b.isShaderMaterial&&!b.isRawShaderMaterial||b.clipping===!0)&&(Ee.clippingPlanes=se.uniform),Oc(b,xe),G.needsLights=wh(b),G.lightsStateVersion=ce,G.needsLights&&(Ee.ambientLightColor.value=O.state.ambient,Ee.lightProbe.value=O.state.probe,Ee.directionalLights.value=O.state.directional,Ee.directionalLightShadows.value=O.state.directionalShadow,Ee.spotLights.value=O.state.spot,Ee.spotLightShadows.value=O.state.spotShadow,Ee.rectAreaLights.value=O.state.rectArea,Ee.ltc_1.value=O.state.rectAreaLTC1,Ee.ltc_2.value=O.state.rectAreaLTC2,Ee.pointLights.value=O.state.point,Ee.pointLightShadows.value=O.state.pointShadow,Ee.hemisphereLights.value=O.state.hemi,Ee.directionalShadowMap.value=O.state.directionalShadowMap,Ee.directionalShadowMatrix.value=O.state.directionalShadowMatrix,Ee.spotShadowMap.value=O.state.spotShadowMap,Ee.spotLightMatrix.value=O.state.spotLightMatrix,Ee.spotLightMap.value=O.state.spotLightMap,Ee.pointShadowMap.value=O.state.pointShadowMap,Ee.pointShadowMatrix.value=O.state.pointShadowMatrix),G.currentProgram=Pe,G.uniformsList=null,Pe}function Uc(b){if(b.uniformsList===null){let U=b.currentProgram.getUniforms();b.uniformsList=wr.seqWithValue(U.seq,b.uniforms)}return b.uniformsList}function Oc(b,U){let V=ve.get(b);V.outputColorSpace=U.outputColorSpace,V.batching=U.batching,V.batchingColor=U.batchingColor,V.instancing=U.instancing,V.instancingColor=U.instancingColor,V.instancingMorph=U.instancingMorph,V.skinning=U.skinning,V.morphTargets=U.morphTargets,V.morphNormals=U.morphNormals,V.morphColors=U.morphColors,V.morphTargetsCount=U.morphTargetsCount,V.numClippingPlanes=U.numClippingPlanes,V.numIntersection=U.numClipIntersection,V.vertexAlphas=U.vertexAlphas,V.vertexTangents=U.vertexTangents,V.toneMapping=U.toneMapping}function vh(b,U,V,G,O){U.isScene!==!0&&(U=ge),ke.resetTextureUnits();let te=U.fog,ce=G.isMeshStandardMaterial?U.environment:null,xe=P===null?y.outputColorSpace:P.isXRRenderTarget===!0?P.texture.colorSpace:Si,he=(G.isMeshStandardMaterial?vt:At).get(G.envMap||ce),Ae=G.vertexColors===!0&&!!V.attributes.color&&V.attributes.color.itemSize===4,Pe=!!V.attributes.tangent&&(!!G.normalMap||G.anisotropy>0),Ee=!!V.morphAttributes.position,We=!!V.morphAttributes.normal,Qe=!!V.morphAttributes.color,_t=$n;G.toneMapped&&(P===null||P.isXRRenderTarget===!0)&&(_t=y.toneMapping);let it=V.morphAttributes.position||V.morphAttributes.normal||V.morphAttributes.color,et=it!==void 0?it.length:0,Te=ve.get(G),ht=f.state.lights;if(Fe===!0&&(Y===!0||b!==v)){let Ut=b===v&&G.id===w;se.setState(G,b,Ut)}let qe=!1;G.version===Te.__version?(Te.needsLights&&Te.lightsStateVersion!==ht.state.version||Te.outputColorSpace!==xe||O.isBatchedMesh&&Te.batching===!1||!O.isBatchedMesh&&Te.batching===!0||O.isBatchedMesh&&Te.batchingColor===!0&&O.colorTexture===null||O.isBatchedMesh&&Te.batchingColor===!1&&O.colorTexture!==null||O.isInstancedMesh&&Te.instancing===!1||!O.isInstancedMesh&&Te.instancing===!0||O.isSkinnedMesh&&Te.skinning===!1||!O.isSkinnedMesh&&Te.skinning===!0||O.isInstancedMesh&&Te.instancingColor===!0&&O.instanceColor===null||O.isInstancedMesh&&Te.instancingColor===!1&&O.instanceColor!==null||O.isInstancedMesh&&Te.instancingMorph===!0&&O.morphTexture===null||O.isInstancedMesh&&Te.instancingMorph===!1&&O.morphTexture!==null||Te.envMap!==he||G.fog===!0&&Te.fog!==te||Te.numClippingPlanes!==void 0&&(Te.numClippingPlanes!==se.numPlanes||Te.numIntersection!==se.numIntersection)||Te.vertexAlphas!==Ae||Te.vertexTangents!==Pe||Te.morphTargets!==Ee||Te.morphNormals!==We||Te.morphColors!==Qe||Te.toneMapping!==_t||Te.morphTargetsCount!==et)&&(qe=!0):(qe=!0,Te.__version=G.version);let Jt=Te.currentProgram;qe===!0&&(Jt=Rs(G,U,O));let Vi=!1,Kt=!1,Rr=!1,ft=Jt.getUniforms(),an=Te.uniforms;if(ye.useProgram(Jt.program)&&(Vi=!0,Kt=!0,Rr=!0),G.id!==w&&(w=G.id,Kt=!0),Vi||v!==b){ye.buffers.depth.getReversed()&&b.reversedDepth!==!0&&(b._reversedDepth=!0,b.updateProjectionMatrix()),ft.setValue(I,"projectionMatrix",b.projectionMatrix),ft.setValue(I,"viewMatrix",b.matrixWorldInverse);let Vt=ft.map.cameraPosition;Vt!==void 0&&Vt.setValue(I,pe.setFromMatrixPosition(b.matrixWorld)),Ie.logarithmicDepthBuffer&&ft.setValue(I,"logDepthBufFC",2/(Math.log(b.far+1)/Math.LN2)),(G.isMeshPhongMaterial||G.isMeshToonMaterial||G.isMeshLambertMaterial||G.isMeshBasicMaterial||G.isMeshStandardMaterial||G.isShaderMaterial)&&ft.setValue(I,"isOrthographic",b.isOrthographicCamera===!0),v!==b&&(v=b,Kt=!0,Rr=!0)}if(O.isSkinnedMesh){ft.setOptional(I,O,"bindMatrix"),ft.setOptional(I,O,"bindMatrixInverse");let Ut=O.skeleton;Ut&&(Ut.boneTexture===null&&Ut.computeBoneTexture(),ft.setValue(I,"boneTexture",Ut.boneTexture,ke))}O.isBatchedMesh&&(ft.setOptional(I,O,"batchingTexture"),ft.setValue(I,"batchingTexture",O._matricesTexture,ke),ft.setOptional(I,O,"batchingIdTexture"),ft.setValue(I,"batchingIdTexture",O._indirectTexture,ke),ft.setOptional(I,O,"batchingColorTexture"),O._colorsTexture!==null&&ft.setValue(I,"batchingColorTexture",O._colorsTexture,ke));let on=V.morphAttributes;if((on.position!==void 0||on.normal!==void 0||on.color!==void 0)&&ie.update(O,V,Jt),(Kt||Te.receiveShadow!==O.receiveShadow)&&(Te.receiveShadow=O.receiveShadow,ft.setValue(I,"receiveShadow",O.receiveShadow)),G.isMeshGouraudMaterial&&G.envMap!==null&&(an.envMap.value=he,an.flipEnvMap.value=he.isCubeTexture&&he.isRenderTargetTexture===!1?-1:1),G.isMeshStandardMaterial&&G.envMap===null&&U.environment!==null&&(an.envMapIntensity.value=U.environmentIntensity),Kt&&(ft.setValue(I,"toneMappingExposure",y.toneMappingExposure),Te.needsLights&&bh(an,Rr),te&&G.fog===!0&&K.refreshFogUniforms(an,te),K.refreshMaterialUniforms(an,G,H,X,f.state.transmissionRenderTarget[b.id]),wr.upload(I,Uc(Te),an,ke)),G.isShaderMaterial&&G.uniformsNeedUpdate===!0&&(wr.upload(I,Uc(Te),an,ke),G.uniformsNeedUpdate=!1),G.isSpriteMaterial&&ft.setValue(I,"center",O.center),ft.setValue(I,"modelViewMatrix",O.modelViewMatrix),ft.setValue(I,"normalMatrix",O.normalMatrix),ft.setValue(I,"modelMatrix",O.matrixWorld),G.isShaderMaterial||G.isRawShaderMaterial){let Ut=G.uniformsGroups;for(let Vt=0,$o=Ut.length;Vt<$o;Vt++){let gi=Ut[Vt];Be.update(gi,Jt),Be.bind(gi,Jt)}}return Jt}function bh(b,U){b.ambientLightColor.needsUpdate=U,b.lightProbe.needsUpdate=U,b.directionalLights.needsUpdate=U,b.directionalLightShadows.needsUpdate=U,b.pointLights.needsUpdate=U,b.pointLightShadows.needsUpdate=U,b.spotLights.needsUpdate=U,b.spotLightShadows.needsUpdate=U,b.rectAreaLights.needsUpdate=U,b.hemisphereLights.needsUpdate=U}function wh(b){return b.isMeshLambertMaterial||b.isMeshToonMaterial||b.isMeshPhongMaterial||b.isMeshStandardMaterial||b.isShadowMaterial||b.isShaderMaterial&&b.lights===!0}this.getActiveCubeFace=function(){return E},this.getActiveMipmapLevel=function(){return R},this.getRenderTarget=function(){return P},this.setRenderTargetTextures=function(b,U,V){let G=ve.get(b);G.__autoAllocateDepthBuffer=b.resolveDepthBuffer===!1,G.__autoAllocateDepthBuffer===!1&&(G.__useRenderToTexture=!1),ve.get(b.texture).__webglTexture=U,ve.get(b.depthTexture).__webglTexture=G.__autoAllocateDepthBuffer?void 0:V,G.__hasExternalTextures=!0},this.setRenderTargetFramebuffer=function(b,U){let V=ve.get(b);V.__webglFramebuffer=U,V.__useDefaultFramebuffer=U===void 0};let Mh=I.createFramebuffer();this.setRenderTarget=function(b,U=0,V=0){P=b,E=U,R=V;let G=!0,O=null,te=!1,ce=!1;if(b){let he=ve.get(b);if(he.__useDefaultFramebuffer!==void 0)ye.bindFramebuffer(I.FRAMEBUFFER,null),G=!1;else if(he.__webglFramebuffer===void 0)ke.setupRenderTarget(b);else if(he.__hasExternalTextures)ke.rebindTextures(b,ve.get(b.texture).__webglTexture,ve.get(b.depthTexture).__webglTexture);else if(b.depthBuffer){let Ee=b.depthTexture;if(he.__boundDepthTexture!==Ee){if(Ee!==null&&ve.has(Ee)&&(b.width!==Ee.image.width||b.height!==Ee.image.height))throw new Error("WebGLRenderTarget: Attached DepthTexture is initialized to the incorrect size.");ke.setupDepthRenderbuffer(b)}}let Ae=b.texture;(Ae.isData3DTexture||Ae.isDataArrayTexture||Ae.isCompressedArrayTexture)&&(ce=!0);let Pe=ve.get(b).__webglFramebuffer;b.isWebGLCubeRenderTarget?(Array.isArray(Pe[U])?O=Pe[U][V]:O=Pe[U],te=!0):b.samples>0&&ke.useMultisampledRTT(b)===!1?O=ve.get(b).__webglMultisampledFramebuffer:Array.isArray(Pe)?O=Pe[V]:O=Pe,T.copy(b.viewport),D.copy(b.scissor),F=b.scissorTest}else T.copy(fe).multiplyScalar(H).floor(),D.copy(De).multiplyScalar(H).floor(),F=Xe;if(V!==0&&(O=Mh),ye.bindFramebuffer(I.FRAMEBUFFER,O)&&G&&ye.drawBuffers(b,O),ye.viewport(T),ye.scissor(D),ye.setScissorTest(F),te){let he=ve.get(b.texture);I.framebufferTexture2D(I.FRAMEBUFFER,I.COLOR_ATTACHMENT0,I.TEXTURE_CUBE_MAP_POSITIVE_X+U,he.__webglTexture,V)}else if(ce){let he=U;for(let Ae=0;Ae<b.textures.length;Ae++){let Pe=ve.get(b.textures[Ae]);I.framebufferTextureLayer(I.FRAMEBUFFER,I.COLOR_ATTACHMENT0+Ae,Pe.__webglTexture,V,he)}}else if(b!==null&&V!==0){let he=ve.get(b.texture);I.framebufferTexture2D(I.FRAMEBUFFER,I.COLOR_ATTACHMENT0,I.TEXTURE_2D,he.__webglTexture,V)}w=-1},this.readRenderTargetPixels=function(b,U,V,G,O,te,ce,xe=0){if(!(b&&b.isWebGLRenderTarget)){console.error("THREE.WebGLRenderer.readRenderTargetPixels: renderTarget is not THREE.WebGLRenderTarget.");return}let he=ve.get(b).__webglFramebuffer;if(b.isWebGLCubeRenderTarget&&ce!==void 0&&(he=he[ce]),he){ye.bindFramebuffer(I.FRAMEBUFFER,he);try{let Ae=b.textures[xe],Pe=Ae.format,Ee=Ae.type;if(!Ie.textureFormatReadable(Pe)){console.error("THREE.WebGLRenderer.readRenderTargetPixels: renderTarget is not in RGBA or implementation defined format.");return}if(!Ie.textureTypeReadable(Ee)){console.error("THREE.WebGLRenderer.readRenderTargetPixels: renderTarget is not in UnsignedByteType or implementation defined type.");return}U>=0&&U<=b.width-G&&V>=0&&V<=b.height-O&&(b.textures.length>1&&I.readBuffer(I.COLOR_ATTACHMENT0+xe),I.readPixels(U,V,G,O,Me.convert(Pe),Me.convert(Ee),te))}finally{let Ae=P!==null?ve.get(P).__webglFramebuffer:null;ye.bindFramebuffer(I.FRAMEBUFFER,Ae)}}},this.readRenderTargetPixelsAsync=async function(b,U,V,G,O,te,ce,xe=0){if(!(b&&b.isWebGLRenderTarget))throw new Error("THREE.WebGLRenderer.readRenderTargetPixels: renderTarget is not THREE.WebGLRenderTarget.");let he=ve.get(b).__webglFramebuffer;if(b.isWebGLCubeRenderTarget&&ce!==void 0&&(he=he[ce]),he)if(U>=0&&U<=b.width-G&&V>=0&&V<=b.height-O){ye.bindFramebuffer(I.FRAMEBUFFER,he);let Ae=b.textures[xe],Pe=Ae.format,Ee=Ae.type;if(!Ie.textureFormatReadable(Pe))throw new Error("THREE.WebGLRenderer.readRenderTargetPixelsAsync: renderTarget is not in RGBA or implementation defined format.");if(!Ie.textureTypeReadable(Ee))throw new Error("THREE.WebGLRenderer.readRenderTargetPixelsAsync: renderTarget is not in UnsignedByteType or implementation defined type.");let We=I.createBuffer();I.bindBuffer(I.PIXEL_PACK_BUFFER,We),I.bufferData(I.PIXEL_PACK_BUFFER,te.byteLength,I.STREAM_READ),b.textures.length>1&&I.readBuffer(I.COLOR_ATTACHMENT0+xe),I.readPixels(U,V,G,O,Me.convert(Pe),Me.convert(Ee),0);let Qe=P!==null?ve.get(P).__webglFramebuffer:null;ye.bindFramebuffer(I.FRAMEBUFFER,Qe);let _t=I.fenceSync(I.SYNC_GPU_COMMANDS_COMPLETE,0);return I.flush(),await tu(I,_t,4),I.bindBuffer(I.PIXEL_PACK_BUFFER,We),I.getBufferSubData(I.PIXEL_PACK_BUFFER,0,te),I.deleteBuffer(We),I.deleteSync(_t),te}else throw new Error("THREE.WebGLRenderer.readRenderTargetPixelsAsync: requested read bounds are out of range.")},this.copyFramebufferToTexture=function(b,U=null,V=0){let G=Math.pow(2,-V),O=Math.floor(b.image.width*G),te=Math.floor(b.image.height*G),ce=U!==null?U.x:0,xe=U!==null?U.y:0;ke.setTexture2D(b,0),I.copyTexSubImage2D(I.TEXTURE_2D,V,0,0,ce,xe,O,te),ye.unbindTexture()};let Sh=I.createFramebuffer(),Eh=I.createFramebuffer();this.copyTextureToTexture=function(b,U,V=null,G=null,O=0,te=null){te===null&&(O!==0?(cr("WebGLRenderer: copyTextureToTexture function signature has changed to support src and dst mipmap levels."),te=O,O=0):te=0);let ce,xe,he,Ae,Pe,Ee,We,Qe,_t,it=b.isCompressedTexture?b.mipmaps[te]:b.image;if(V!==null)ce=V.max.x-V.min.x,xe=V.max.y-V.min.y,he=V.isBox3?V.max.z-V.min.z:1,Ae=V.min.x,Pe=V.min.y,Ee=V.isBox3?V.min.z:0;else{let on=Math.pow(2,-O);ce=Math.floor(it.width*on),xe=Math.floor(it.height*on),b.isDataArrayTexture?he=it.depth:b.isData3DTexture?he=Math.floor(it.depth*on):he=1,Ae=0,Pe=0,Ee=0}G!==null?(We=G.x,Qe=G.y,_t=G.z):(We=0,Qe=0,_t=0);let et=Me.convert(U.format),Te=Me.convert(U.type),ht;U.isData3DTexture?(ke.setTexture3D(U,0),ht=I.TEXTURE_3D):U.isDataArrayTexture||U.isCompressedArrayTexture?(ke.setTexture2DArray(U,0),ht=I.TEXTURE_2D_ARRAY):(ke.setTexture2D(U,0),ht=I.TEXTURE_2D),I.pixelStorei(I.UNPACK_FLIP_Y_WEBGL,U.flipY),I.pixelStorei(I.UNPACK_PREMULTIPLY_ALPHA_WEBGL,U.premultiplyAlpha),I.pixelStorei(I.UNPACK_ALIGNMENT,U.unpackAlignment);let qe=I.getParameter(I.UNPACK_ROW_LENGTH),Jt=I.getParameter(I.UNPACK_IMAGE_HEIGHT),Vi=I.getParameter(I.UNPACK_SKIP_PIXELS),Kt=I.getParameter(I.UNPACK_SKIP_ROWS),Rr=I.getParameter(I.UNPACK_SKIP_IMAGES);I.pixelStorei(I.UNPACK_ROW_LENGTH,it.width),I.pixelStorei(I.UNPACK_IMAGE_HEIGHT,it.height),I.pixelStorei(I.UNPACK_SKIP_PIXELS,Ae),I.pixelStorei(I.UNPACK_SKIP_ROWS,Pe),I.pixelStorei(I.UNPACK_SKIP_IMAGES,Ee);let ft=b.isDataArrayTexture||b.isData3DTexture,an=U.isDataArrayTexture||U.isData3DTexture;if(b.isDepthTexture){let on=ve.get(b),Ut=ve.get(U),Vt=ve.get(on.__renderTarget),$o=ve.get(Ut.__renderTarget);ye.bindFramebuffer(I.READ_FRAMEBUFFER,Vt.__webglFramebuffer),ye.bindFramebuffer(I.DRAW_FRAMEBUFFER,$o.__webglFramebuffer);for(let gi=0;gi<he;gi++)ft&&(I.framebufferTextureLayer(I.READ_FRAMEBUFFER,I.COLOR_ATTACHMENT0,ve.get(b).__webglTexture,O,Ee+gi),I.framebufferTextureLayer(I.DRAW_FRAMEBUFFER,I.COLOR_ATTACHMENT0,ve.get(U).__webglTexture,te,_t+gi)),I.blitFramebuffer(Ae,Pe,ce,xe,We,Qe,ce,xe,I.DEPTH_BUFFER_BIT,I.NEAREST);ye.bindFramebuffer(I.READ_FRAMEBUFFER,null),ye.bindFramebuffer(I.DRAW_FRAMEBUFFER,null)}else if(O!==0||b.isRenderTargetTexture||ve.has(b)){let on=ve.get(b),Ut=ve.get(U);ye.bindFramebuffer(I.READ_FRAMEBUFFER,Sh),ye.bindFramebuffer(I.DRAW_FRAMEBUFFER,Eh);for(let Vt=0;Vt<he;Vt++)ft?I.framebufferTextureLayer(I.READ_FRAMEBUFFER,I.COLOR_ATTACHMENT0,on.__webglTexture,O,Ee+Vt):I.framebufferTexture2D(I.READ_FRAMEBUFFER,I.COLOR_ATTACHMENT0,I.TEXTURE_2D,on.__webglTexture,O),an?I.framebufferTextureLayer(I.DRAW_FRAMEBUFFER,I.COLOR_ATTACHMENT0,Ut.__webglTexture,te,_t+Vt):I.framebufferTexture2D(I.DRAW_FRAMEBUFFER,I.COLOR_ATTACHMENT0,I.TEXTURE_2D,Ut.__webglTexture,te),O!==0?I.blitFramebuffer(Ae,Pe,ce,xe,We,Qe,ce,xe,I.COLOR_BUFFER_BIT,I.NEAREST):an?I.copyTexSubImage3D(ht,te,We,Qe,_t+Vt,Ae,Pe,ce,xe):I.copyTexSubImage2D(ht,te,We,Qe,Ae,Pe,ce,xe);ye.bindFramebuffer(I.READ_FRAMEBUFFER,null),ye.bindFramebuffer(I.DRAW_FRAMEBUFFER,null)}else an?b.isDataTexture||b.isData3DTexture?I.texSubImage3D(ht,te,We,Qe,_t,ce,xe,he,et,Te,it.data):U.isCompressedArrayTexture?I.compressedTexSubImage3D(ht,te,We,Qe,_t,ce,xe,he,et,it.data):I.texSubImage3D(ht,te,We,Qe,_t,ce,xe,he,et,Te,it):b.isDataTexture?I.texSubImage2D(I.TEXTURE_2D,te,We,Qe,ce,xe,et,Te,it.data):b.isCompressedTexture?I.compressedTexSubImage2D(I.TEXTURE_2D,te,We,Qe,it.width,it.height,et,it.data):I.texSubImage2D(I.TEXTURE_2D,te,We,Qe,ce,xe,et,Te,it);I.pixelStorei(I.UNPACK_ROW_LENGTH,qe),I.pixelStorei(I.UNPACK_IMAGE_HEIGHT,Jt),I.pixelStorei(I.UNPACK_SKIP_PIXELS,Vi),I.pixelStorei(I.UNPACK_SKIP_ROWS,Kt),I.pixelStorei(I.UNPACK_SKIP_IMAGES,Rr),te===0&&U.generateMipmaps&&I.generateMipmap(ht),ye.unbindTexture()},this.initRenderTarget=function(b){ve.get(b).__webglFramebuffer===void 0&&ke.setupRenderTarget(b)},this.initTexture=function(b){b.isCubeTexture?ke.setTextureCube(b,0):b.isData3DTexture?ke.setTexture3D(b,0):b.isDataArrayTexture||b.isCompressedArrayTexture?ke.setTexture2DArray(b,0):ke.setTexture2D(b,0),ye.unbindTexture()},this.resetState=function(){E=0,R=0,P=null,ye.reset(),le.reset()},typeof __THREE_DEVTOOLS__<"u"&&__THREE_DEVTOOLS__.dispatchEvent(new CustomEvent("observe",{detail:this}))}get coordinateSystem(){return yn}get outputColorSpace(){return this._outputColorSpace}set outputColorSpace(e){this._outputColorSpace=e;let t=this.getContext();t.drawingBufferColorSpace=$e._getDrawingBufferColorSpace(e),t.unpackColorSpace=$e._getUnpackColorSpace()}};var j=i=>document.getElementById(i),bc=Object.create(null),J0={camera:5,yolo:5,midas:5,odometry:5,segmentation:5,radar:2,gps:5,imu:2,tof:2},Lu=["camera","radar","gps","imu","tof","lidar","ultrasonic"],bs={horizontalFovDeg:70,yawOffsetDeg:0,lateralOffsetM:0,calibrated:!1},Sr=.25,K0=8,No=.5,j0=5;function Tt(i,e,t,n){bc[e]=t;let r=j(i);if(r){r.dataset.state=t;let l=t==="live"?"LIVE":t==="stale"?"STALE":t==="offline"?"OFFLINE":"LOADING";r.textContent=n.toUpperCase().startsWith(`${l} \xB7`)?n:`${l} \xB7 ${n}`}let s=e==="tof"?r?.closest(".sensor-readout-card"):null;if(s){let l=document.querySelector('.world-map-offline-pill[data-source="tof"]');if(s.hidden=t!=="live",l){l.hidden=t==="live";let c=l.querySelector("[data-offline-reason]");c&&(c.textContent=n)}}let a=Lu.filter(l=>bc[l]==="live").length,o=j("world-map-summary-live");o&&(o.textContent=`${a} / ${Lu.length}`)}var Jn=(i,e,t)=>t?Number.isFinite(e)&&e>J0[i]?"stale":"live":"offline",hc=new Set;function Do(i,e){e?hc.add(i):hc.delete(i);let t=j("world-map-cloud-fetch");t&&(t.hidden=hc.size===0)}var Zt=null,wc=0,fc=!1,pi=null,Ss=null,Cr=null,kt=null,pc="",Fu=null,Uu="",Ou="",Li=[],Q0=1,at=null,mc=0,Io="",Mc="",Ht=null,ws=!1,Er="",Yn=[],Bu="",hn=null,Sn=null,Tr=[],mt=0,Fi=[],Ju=0,ys=[];function ex(i,e=.2){let t=Number(i);if(!Number.isFinite(t))return null;let n=Fi.filter(l=>l.attitude_valid&&Number.isFinite(Number(l.timestamp))&&Number.isFinite(Number(l.roll_deg))&&Number.isFinite(Number(l.pitch_deg)));if(!n.length)return null;let r=null,s=null;for(let l of n){let c=Number(l.timestamp);c<=t&&(!r||c>Number(r.timestamp))&&(r=l),c>=t&&(!s||c<Number(s.timestamp))&&(s=l)}let a=(l,c)=>(c-l+540)%360-180;if(r&&s&&Number(s.timestamp)-Number(r.timestamp)<=.25){let l=Number(s.timestamp)-Number(r.timestamp),c=l>0?(t-Number(r.timestamp))/l:0,d=u=>Number(r[u])+a(Number(r[u]),Number(s[u]))*c;return{roll_deg:d("roll_deg"),pitch_deg:d("pitch_deg"),timestamp:t}}let o=n.reduce((l,c)=>!l||Math.abs(Number(c.timestamp)-t)<Math.abs(Number(l.timestamp)-t)?c:l,null);return Math.abs(Number(o.timestamp)-t)<=e?o:null}function Rc(i){let e=ex(i);return e?new Wt().setFromEuler(new en(yt.degToRad(Number(e.roll_deg)),yt.degToRad(Number(e.pitch_deg)),0,"XYZ")):null}function tx(i,e=.1){let t=Number(i);return Tr.reduce((n,r)=>{let s=Math.abs(Number(r.timestamp)-t);return s<=e&&(!n||s<n.age)?{sample:r,age:s}:n},null)?.sample||null}var fn=document.querySelector("#view-worldmodel .map-panel");if(fn){let i=fn.querySelector(".panel-head"),e=fn.querySelector(".map-layout"),t=fn.querySelector(".map-wrap"),n=fn.querySelector(".map-intro");if(i&&e&&t&&!j("world-map-source")){let r=document.createElement("div");r.className="world-map-controls",r.innerHTML='<div class="world-map-segment" role="group" aria-label="Map rendering"><button type="button" data-render="2d" aria-pressed="true">2D</button><button type="button" data-render="3d" aria-pressed="false">3D</button></div><small id="world-map-state" role="status">Simulation \xB7 2D</small>',i.append(r);let s=document.createElement("div");s.id="world-map-sim-3d",s.className="world-map-canvas",s.hidden=!0,e.insertBefore(s,t);let a=document.createElement("section");a.id="world-map-sensor-view",a.className="world-map-sensor-view",a.hidden=!0,a.innerHTML='<div class="world-map-sensor-metrics"><span>Camera <b id="world-map-camera-state">Waiting</b></span><span>YOLOX <b id="world-map-yolo-state">Waiting</b></span><span>MiDaS <b id="world-map-midas-state">Waiting</b></span><span>Visual odometry <b id="world-map-odometry-state">Waiting</b></span><span>SegFormer <b id="world-map-segmentation-state">disabled</b></span><span>Frame <b id="world-map-frame-state">\u2014</b></span></div><div id="world-map-sensor-2d" class="world-map-sensor-2d"><div class="world-map-camera"><div class="world-map-sensor-heading">CAMERA \xB7 YOLOX</div><div class="world-map-image-wrap"><img id="world-map-camera-image" alt="Live camera frame with YOLOX detections"><svg id="world-map-yolo-overlay" viewBox="0 0 1 1" preserveAspectRatio="xMidYMid meet" aria-hidden="true"></svg><span id="world-map-camera-empty" class="world-map-empty">Waiting for a camera frame</span></div></div><div class="world-map-depth"><div class="world-map-sensor-heading">MiDaS \xB7 RELATIVE DEPTH</div><img id="world-map-depth-image" alt="MiDaS relative depth image"><span id="world-map-depth-empty" class="world-map-empty">MiDaS disabled or waiting for inference</span><div class="world-map-depth-calibration"><button type="button" id="world-map-midas-calibrate">Calibrate with radar</button><small id="world-map-midas-calibration-status" role="status">Relative depth only \xB7 not calibrated in metres</small></div></div></div><section class="world-map-odometry-view" aria-label="Experimental visual odometry trajectory"><div class="world-map-sensor-heading"><span>VISUAL ODOMETRY \xB7 LOCAL TRAJECTORY</span><small id="world-map-odometry-map-status">Waiting for tracking</small></div><div class="odom-plot"><canvas id="world-map-odometry-map" role="img" aria-label="Top-down estimated Body trajectory in the local visual odometry frame"></canvas><span class="odom-edge-label odom-forward">FORWARD \u2191</span><span class="odom-edge-label odom-lateral">\u2190 LEFT \xB7 RIGHT \u2192</span><span id="world-map-odometry-position" class="odom-position-label">0.00, 0.00 m</span></div><p class="world-map-odometry-footnote">Session-local estimate \xB7 drift accumulates \xB7 not a persistent map</p></section><section class="world-map-segmentation-panel" aria-label="SegFormer semantic segmentation"><div class="world-map-sensor-heading"><span>SEGFORMER \xB7 SEMANTIC MASK</span><small>Independent of camera preview</small></div><div class="world-map-segmentation-preview"><canvas id="world-map-segmentation-overlay" aria-label="Standalone SegFormer semantic class mask" hidden></canvas><span id="world-map-segmentation-empty" class="world-map-empty">Waiting for a SegFormer mask</span></div><div id="world-map-segmentation-classes" class="world-map-segmentation-classes">Waiting for SegFormer classes</div></section><div id="world-map-sensor-3d" class="world-map-sensor-cloud-layout" hidden><div id="world-map-sensor-3d-viewport" class="world-map-canvas world-map-sensor-cloud"><div class="world-map-cloud-hud"><span id="world-map-cloud-hud-points">0 points</span><span id="world-map-cloud-hud-depth">MiDaS \u2014</span><span id="world-map-cloud-hud-age">Frame \u2014</span><span id="world-map-cloud-hud-sync">Camera/depth \u2014</span><span id="world-map-cloud-hud-pipeline">Pipeline \u2014</span><span id="world-map-cloud-hud-fps">3D \u2014 FPS</span><div class="world-map-cloud-stale" id="world-map-cloud-stale" hidden role="status"></div></div><div class="world-map-cloud-controls"><button type="button" data-cloud-action="reset" title="Reset camera to fit point cloud">Reset</button><button type="button" data-cloud-view="camera" title="Pinhole camera view; FOV is estimated unless intrinsics are provided">Camera</button><button type="button" data-cloud-view="top">Top</button><button type="button" data-cloud-view="side">Side</button><button type="button" data-cloud-view="follow">Follow</button><label>Point size <input id="world-map-cloud-point-size" type="range" min="10" max="50" value="25" aria-label="3D point size"></label></div><div class="world-map-cloud-labels" aria-hidden="true"></div><div class="world-map-cloud-scale" hidden>1 m</div><div id="world-map-cloud-fetch" class="world-map-cloud-fetch" hidden>Sensor data unavailable: fetch failed, retrying</div></div><aside class="world-map-cloud-side"><strong>Scene layers</strong><label><input type="checkbox" data-cloud-layer="cloud" checked> MiDaS point cloud</label><label><input type="checkbox" data-cloud-layer="detections" checked> YOLOX detections</label><label><input type="checkbox" data-cloud-layer="radar" checked> mmWave targets (metres)</label><label><input type="checkbox" data-cloud-layer="odometry" checked> Odometry trail</label><strong>Depth units</strong><div class="world-map-depth-legend"><i></i><div><span>Near</span><span>Far</span></div></div><small id="world-map-cloud-depth-caption">Relative units \xB7 not metric</small><small>Radar markers use metres, independently scaled from an uncalibrated MiDaS cloud.</small><div class="world-map-depth-calibration"><button type="button" id="world-map-midas-calibrate-3d">Calibrate with radar</button><small id="world-map-midas-calibration-status-3d" role="status">Relative depth only \xB7 not calibrated in metres</small></div><div class="world-map-cloud-axis" aria-label="XYZ orientation: X right, Y up, Z forward"><span>X \u2192</span><span>Y \u2191</span><span>Z \u2299</span></div></aside></div><p id="world-map-sensor-note" class="world-map-sensor-note">Sensor-only view \xB7 no simulation object positions are used.</p>',a.querySelector('[data-cloud-layer="radar"]').checked=!0,a.querySelector("#world-map-cloud-hud-fps").textContent="3D \u2014 FPS";for(let T of["world-map-camera-state","world-map-yolo-state","world-map-midas-state","world-map-odometry-state","world-map-segmentation-state","world-map-radar-state","world-map-gps-state","world-map-imu-state","world-map-tof-state"]){let D=j(T);D&&(D.dataset.state="loading")}let o=document.createElement("section");o.id="world-map-live-readouts",o.className="world-map-live-readouts",o.innerHTML='<article class="sensor-readout-card"><header><strong>mmWave \xB7 LD2450</strong><small id="world-map-radar-state">Waiting</small></header><canvas id="world-map-radar-plot" height="190" aria-label="Live mmWave target positions and radial velocities"></canvas><div id="world-map-radar-targets" class="sensor-target-list">Waiting for radar data.</div></article><article class="sensor-readout-card"><header><strong>GPS / GNSS \xB7 D0/D1</strong><small id="world-map-gps-state">Waiting</small></header><div class="sensor-readout-values"><span>Position<b id="world-map-gps-position">No fix</b></span><span>Fix / quality<b id="world-map-gps-fix">\u2014</b></span><span>Satellites<b id="world-map-gps-satellites">\u2014 used \xB7 \u2014 in view</b></span><span>HDOP / altitude<b id="world-map-gps-quality">\u2014</b></span></div><div id="world-map-gps-signals" class="sensor-gps-signals" role="img" aria-label="GPS satellite signal strength by satellite"></div></article><article class="sensor-readout-card"><header><strong>Modulino Movement \xB7 IMU</strong><small id="world-map-imu-state">Waiting</small></header><div id="world-map-imu-attitude" class="imu-attitude" role="img" aria-label="IMU attitude indicator based on roll and pitch"><div class="imu-attitude-disc" aria-hidden="true"><div class="imu-attitude-horizon"><span></span></div><i class="imu-attitude-mark"></i></div><div><b>ATTITUDE</b><small>Roll / pitch \xB7 no magnetic heading</small></div></div><div class="sensor-readout-values"><span>Roll<b id="world-map-imu-roll">\u2014</b></span><span>Pitch<b id="world-map-imu-pitch">\u2014</b></span><span>Yaw rate<b id="world-map-imu-yaw">\u2014</b></span><span>Acceleration \xB7 g<b id="world-map-imu-accel">\u2014</b></span><span>Angular rate \xB7 \xB0/s<b id="world-map-imu-gyro">\u2014</b></span></div><p class="sensor-readout-note">Six-axis IMU; yaw is relative angular rate, not a magnetic heading.</p></article><article class="sensor-readout-card"><header><strong>ToF \xB7 VL53L1X</strong><small id="world-map-tof-state">Waiting</small></header><div class="sensor-distance"><b id="world-map-tof-distance">\u2014</b><span id="world-map-tof-meta">Forward single-beam range</span></div></article><article class="sensor-readout-card"><header><strong>LiDAR</strong><small id="world-map-lidar-state">No live source</small></header><p class="sensor-readout-note">No physical LiDAR stream is connected to this Body view. Any LiDAR volume shown in Simulation is virtual and is kept out of this live sensor view.</p></article><article class="sensor-readout-card"><header><strong>Ultrasonic \xB7 HC-SR04</strong><small id="world-map-ultrasonic-state">No live source</small></header><div class="sensor-readout-values sensor-range-channels"><span>Front-left<b id="world-map-ultrasonic-left">No data</b></span><span>Front-right<b id="world-map-ultrasonic-right">No data</b></span><span>Rear<b id="world-map-ultrasonic-rear">No data</b></span></div><p class="sensor-readout-note">Waiting for the ultrasonic firmware/gateway data channel; no simulated ranges are shown here.</p></article>';let l=(T,D)=>{let F=o.querySelector(`#${T}`),B=F?.closest("header"),k=B?.querySelector("strong");if(!F||!B||!k)return;let W=document.createElement("div");W.className="sensor-heading-copy",k.title=D;let X=document.createElement("span");X.className="sensor-card-source",X.textContent=D,X.title=D,W.append(k,X),F.classList.add("sensor-state-chip"),B.replaceChildren(W,F)};l("world-map-radar-state","hlk_ld2450_ventuno_bridge"),l("world-map-gps-state","Serial1 USART3 \xB7 D0/D1 via Ventuno STM32 Bridge"),l("world-map-imu-state","Arduino Modulino Movement / LSM6DSOX");let c=document.createElement("article");c.id="world-map-compute-power",c.className="sensor-readout-card world-map-compute-card",c.innerHTML='<header><strong>Compute & power</strong><small id="world-map-system-state">Sampling</small></header><div class="system-instrument-grid"><article class="system-instrument"><span class="system-instrument-label">CPU LOAD</span><div class="system-gauge" id="world-map-cpu-gauge" role="img" aria-label="CPU utilization"><div class="system-gauge-center"><strong id="world-map-system-cpu-value">\u2014</strong><small>%</small></div></div><span class="system-instrument-foot" id="world-map-system-cpu-temp">CPU temp \xB7 \u2014</span></article><article class="system-instrument"><span class="system-instrument-label">CPU TEMP</span><div class="system-gauge system-gauge-temp" id="world-map-cpu-temp-gauge" role="img" aria-label="Maximum CPU temperature"><div class="system-gauge-center"><strong id="world-map-system-cpu-temp-value">\u2014</strong><small>\xB0C</small></div></div><span class="system-instrument-foot">Hottest reported CPU sensor \xB7 0\u2013100 \xB0C</span></article><article class="system-instrument"><span class="system-instrument-label">GPU TEMP</span><div class="system-gauge system-gauge-temp" id="world-map-gpu-temp-gauge" role="img" aria-label="Maximum GPU temperature"><div class="system-gauge-center"><strong id="world-map-system-gpu-temp-value">\u2014</strong><small>\xB0C</small></div></div><span class="system-instrument-foot" id="world-map-system-gpu-meta">Load unavailable \xB7 \u2014 MHz</span></article><article class="system-instrument"><span class="system-instrument-label">MEMORY</span><div class="system-gauge" id="world-map-memory-gauge" role="img" aria-label="Memory utilization"><div class="system-gauge-center"><strong id="world-map-system-memory-value">\u2014</strong><small>%</small></div></div><span class="system-instrument-foot" id="world-map-system-memory-meta">\u2014 free</span></article><article class="system-instrument"><span class="system-instrument-label">BOARD INPUT</span><div class="system-gauge system-gauge-power" id="world-map-power-gauge" role="img" aria-label="Measured board input power"><div class="system-gauge-center"><strong id="world-map-system-power-value">\u2014</strong><small>W</small></div></div><span class="system-instrument-foot" id="world-map-system-power-meta">INA232 \xB7 measured rail</span></article></div><div class="system-telemetry-strip"><div><span>GPU utilization</span><strong id="world-map-system-gpu-load">Unavailable</strong></div><div><span>GPU clock</span><strong id="world-map-system-gpu-clock">\u2014</strong></div><div><span>Qualcomm HTP</span><strong id="world-map-system-htp">Waiting for inference status</strong></div><div><span>Energy since Body start</span><strong id="world-map-system-energy">\u2014</strong></div></div><p id="world-map-system-note" class="sensor-readout-note">GPU/HTP usage percentages require kernel counters. Board input may exclude external motor loads.</p>',a.append(o,c);let d=a.querySelector(".world-map-sensor-2d"),u=a.querySelector(".world-map-odometry-view"),h=a.querySelector(".world-map-segmentation-panel"),p=j("world-map-odometry-map");p&&typeof ResizeObserver<"u"&&new ResizeObserver(()=>gh()).observe(p.parentElement);let g=document.createElement("div");g.className="world-map-vision-footer",g.append(a.querySelector("#world-map-sensor-note")),d?.after(g),o.querySelector("#world-map-radar-state")?.closest(".sensor-readout-card")?.classList.remove("sensor-readout-wide"),u&&d?.append(u),h&&d?.append(h);let m=document.createElement("div");m.className="world-map-status-bar",m.setAttribute("aria-label","Live Body and sensor status"),m.innerHTML='<span>BODY <b id="world-map-body-status" data-state="loading">Connecting</b></span><span>BOARD INPUT <b id="world-map-summary-power">\u2014 W</b></span><span>ENERGY <b id="world-map-summary-energy">\u2014 Wh</b></span><span>LATEST FRAME <b id="world-map-summary-frame">\u2014</b></span><span>SENSORS LIVE <b id="world-map-summary-live">0 / 7</b></span>',m.append(a.querySelector("#world-map-cloud-fetch"),a.querySelector(".world-map-sensor-metrics")),a.prepend(m);let f=document.querySelector("#message"),S=()=>{let T=f?.textContent?.trim()||"",D=/connected/i.test(T)&&!/disconnected|not connected/i.test(T),F=j("world-map-body-status");F&&(F.textContent=T||"Status unavailable",F.dataset.state=D?"live":T?"offline":"loading")};f&&new MutationObserver(S).observe(f,{childList:!0,characterData:!0,subtree:!0}),S();let M=document.createElement("div");M.className="world-map-offline-strip",M.setAttribute("aria-label","Offline sensors"),M.innerHTML="<strong>OFFLINE</strong>";let y=(T,D,F)=>{let B=o.querySelector(`#${T}`),k=document.createElement("span");return k.className="world-map-offline-pill",k.title=F,k.innerHTML=`<b>${D}</b> <span>${F}</span>`,B&&(B.dataset.offlinePill="true",k.prepend(B),B.dataset.state="offline",B.textContent="OFFLINE"),bc[D==="LiDAR"?"lidar":"ultrasonic"]="offline",M.append(k),k},C=o.querySelector("#world-map-lidar-state")?.closest(".sensor-readout-card"),E=o.querySelector("#world-map-ultrasonic-state")?.closest(".sensor-readout-card");y("world-map-lidar-state","LiDAR","No physical stream connected"),y("world-map-ultrasonic-state","HC-SR04","Waiting for firmware/gateway channel");let R=document.createElement("span");R.className="world-map-offline-pill",R.dataset.source="tof",R.innerHTML="<b>ToF \xB7 VL53L1X</b> <span data-offline-reason>Sensor not detected</span>",M.append(R);let P=o.querySelector("#world-map-tof-state")?.closest(".sensor-readout-card");P&&(P.hidden=!0,P.dataset.source="tof"),C?.remove(),E?.remove();let w=o.querySelector("#world-map-tof-state")?.closest(".sensor-readout-card");w&&(w.hidden=!0),a.append(M),a.querySelector(".world-map-segmentation-panel .world-map-sensor-heading small")?.remove(),e.after(a);let v=document.createElement("style");v.textContent=`
      .world-map-controls{display:flex;align-items:center;gap:12px;flex-wrap:wrap;margin:10px 0 14px}
      .world-map-segment{display:inline-flex;border:1px solid #416b54;border-radius:4px;overflow:hidden}
      .world-map-segment button{border:0;border-radius:0;background:#101b16;padding:7px 12px;color:#a9c0b2}
      .world-map-segment button+button{border-left:1px solid #416b54}
      .world-map-segment button[aria-pressed="true"]{background:#1a3a29;color:#d9f5e5;box-shadow:inset 0 -2px #77d6a1}
      #world-map-state{color:#8eaa98;font:10px ui-monospace,monospace}
      .world-map-canvas{width:100%;height:clamp(300px,48vh,560px);min-height:280px;overflow:hidden;background:#07120f;border:1px solid #263e32;touch-action:none}
      .world-map-canvas canvas{display:block;width:100%;height:100%}
      .world-map-sensor-view[hidden],.world-map-canvas[hidden],.world-map-sensor-2d[hidden]{display:none!important}
      .map-layout[hidden],.map-layout>.map-wrap[hidden],.map-layout>.world-map-canvas[hidden]{display:none!important}
      .world-map-sensor-metrics{display:flex;gap:8px;flex-wrap:wrap;padding:10px 0;color:#64776c;font:10px ui-monospace,monospace}
      .world-map-sensor-metrics span{padding:6px 9px;border:1px solid #d7e1da;background:#f3f7f4}
      .world-map-sensor-metrics b{color:#183d2d;font-weight:650}
      .world-map-odometry-view{min-width:0;background:#07120f;border:1px solid #263e32}
      .world-map-odometry-view>.world-map-sensor-heading{display:flex;justify-content:space-between;gap:12px;align-items:center}
      .world-map-odometry-view>.world-map-sensor-heading small{color:#a9c0b2;font:10px ui-monospace,monospace}
      #world-map-odometry-map{display:block;width:100%;height:clamp(110px,13vh,150px);background:#07120f}
      .odom-map-bg{fill:#07120f}.odom-grid{fill:none;stroke:#254235;stroke-width:1}.odom-grid .odom-axis{stroke:#48745a;stroke-width:1.5}
      .odom-axis-label,.odom-empty-label{fill:#89a895;font:10px ui-monospace,monospace}.odom-position-label{fill:#dceee3;font:11px ui-monospace,monospace}
      #world-map-odometry-trail{fill:none;stroke:#42d6b1;stroke-width:3;stroke-linecap:round;stroke-linejoin:round}
      #world-map-odometry-start{fill:#edbd69;stroke:#07120f;stroke-width:2}#world-map-odometry-body path{fill:#75dfa2;stroke:#d9f5e5;stroke-width:1.5}
      .world-map-odometry-footnote{margin:0;padding:0 10px 9px;color:#89a895;font:10px ui-monospace,monospace}
      .world-map-sensor-2d{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:12px;align-items:stretch}
      .world-map-analysis-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:12px;margin-top:12px;align-items:start}
      .world-map-analysis-stack{display:grid;min-width:0;gap:12px;align-content:start}
      .world-map-camera,.world-map-depth{min-width:0;position:relative;background:#07120f;border:1px solid #263e32;overflow:hidden}
      .world-map-sensor-heading{display:flex;align-items:center;justify-content:space-between;gap:8px;flex-wrap:wrap;min-width:0;padding:9px 11px;border-bottom:1px solid #263e32;color:#91c9aa;font:10px ui-monospace,monospace}
      .world-map-image-wrap{position:relative;display:grid;place-items:center;width:100%;aspect-ratio:4/3;max-height:500px;background:#020805;overflow:hidden}
      .world-map-image-wrap img{display:block;width:100%;height:100%;object-fit:fill}
      #world-map-yolo-overlay{position:absolute;inset:0;width:100%;height:100%;pointer-events:none}
      #world-map-yolo-overlay.is-stale{opacity:.62}
      .world-map-depth{display:flex;flex-direction:column}
      .world-map-segmentation-classes{display:flex;gap:7px 12px;flex-wrap:wrap;margin:0;padding:8px 10px;color:#b4c9bc;font:10px ui-monospace,monospace;line-height:1.6}
      .world-map-segmentation-classes span{display:inline-flex;align-items:center;gap:5px}
      .world-map-segmentation-classes i{width:8px;height:8px;flex:0 0 8px;border-radius:50%}
      .world-map-segmentation-panel{min-width:0;margin-top:12px;overflow:hidden;border:1px solid #263e32;background:#07120f}
      .world-map-segmentation-preview{position:relative;display:grid;width:100%;aspect-ratio:4/3;min-height:140px;justify-items:stretch;align-items:stretch;overflow:hidden;background:#020805}
      #world-map-segmentation-overlay{display:block;width:100%;height:100%;max-width:100%;object-fit:fill}
      #world-map-segmentation-overlay[hidden]{display:none!important}
      .world-map-depth img{display:block;width:100%;height:100%;min-height:220px;max-height:500px;object-fit:contain;background:#020805}
      .world-map-depth>small{padding:7px 10px;color:#9eb5a6;font:10px ui-monospace,monospace}
      .world-map-depth-calibration{display:flex;align-items:center;gap:9px;flex-wrap:wrap;padding:8px 10px;border-top:1px solid #263e32}
      .world-map-depth-calibration button{border:1px solid #416b54;border-radius:3px;background:#10251a;color:#d9f5e5;padding:7px 10px;cursor:pointer}
      .world-map-depth-calibration button:disabled{opacity:.6;cursor:wait}
      .world-map-depth-calibration small{color:#9eb5a6;font:10px ui-monospace,monospace}
      .world-map-empty{position:absolute;inset:0;display:grid;place-items:center;padding:20px;color:#91a79a;font:11px ui-monospace,monospace;text-align:center;pointer-events:none}
      .world-map-empty[hidden]{display:none}
      .world-map-sensor-note{margin:0;color:#9aafc0;font:12px/1.45 ui-sans-serif,system-ui,sans-serif}
      .world-map-sensor-cloud-layout{display:grid;grid-template-columns:minmax(0,1fr) 320px;gap:16px;width:100%;margin-top:16px}
      .world-map-sensor-cloud-layout[hidden]{display:none!important}
      .world-map-sensor-cloud{position:relative;height:clamp(420px,60vh,720px);min-height:420px}
      .world-map-sensor-cloud.is-camera-view{width:min(100%,960px);height:auto;min-height:0;max-height:none;aspect-ratio:4/3;margin-inline:auto}
      .world-map-cloud-hud,.world-map-cloud-controls{position:absolute;z-index:3;display:flex;align-items:center;gap:8px;font:12px/1.3 ui-monospace,monospace}
      .world-map-cloud-hud{top:12px;left:12px;flex-wrap:wrap;max-width:48%;pointer-events:none}
      .world-map-cloud-hud span,.world-map-cloud-controls button,.world-map-cloud-controls label{padding:6px 8px;border:1px solid #263b50;border-radius:4px;background:#080e18ed;color:#e2edf5}
      .world-map-cloud-hud>span{min-width:0;max-width:100%;white-space:normal;overflow-wrap:anywhere}
      .world-map-cloud-controls{top:12px;right:12px;flex-wrap:wrap;justify-content:flex-end;max-width:48%}
      .world-map-cloud-controls::before{content:"Shift/right drag: pan";padding:6px 8px;border:1px solid #263b50;border-radius:4px;background:#080e18ed;color:#9aafc0;font:12px ui-sans-serif,system-ui,sans-serif}
      .world-map-cloud-controls button{cursor:pointer;font:12px ui-sans-serif,system-ui,sans-serif}
      .world-map-cloud-controls button:hover{border-color:#00d6df}
      .world-map-cloud-controls label{display:flex;align-items:center;gap:6px}
      .world-map-cloud-controls input{width:72px;accent-color:#00d6df}
      .world-map-cloud-hud .world-map-cloud-stale{position:static;z-index:auto;flex:1 0 100%;width:max-content;max-width:100%;padding:7px 10px;border:1px solid #a66d1b;border-radius:4px;background:#30210bee;color:#ffd58a;font:12px/1.35 ui-sans-serif,system-ui,sans-serif;pointer-events:none}
      .world-map-cloud-stale[hidden]{display:none!important}
      .world-map-cloud-labels{position:absolute;inset:0;z-index:2;overflow:hidden;pointer-events:none}
      .world-map-cloud-object-label{position:absolute;width:max-content;max-width:min(260px,calc(100% - 16px));transform:translate(-50%,-100%);padding:4px 7px;border:1px solid #7290a3;border-radius:4px;background:#05070df2;color:#f4f8fb;font:12px/1.25 ui-sans-serif,system-ui,sans-serif;white-space:normal;overflow-wrap:anywhere;text-shadow:0 1px #000}
      .world-map-cloud-object-label::after{position:absolute;top:100%;left:50%;height:9px;border-left:1px solid #a9c6d6;content:""}
      .world-map-cloud-radar-dot{position:absolute;width:16px;height:16px;transform:translate(-50%,-50%);border:2px solid #fff;border-radius:50%;background:#f2bc65;box-shadow:0 0 0 4px #f2bc6566,0 0 16px 5px #f2bc65;z-index:4}
      .world-map-cloud-radar-dot.is-moving{background:#ed35c5;box-shadow:0 0 0 4px #ed35c566,0 0 16px 5px #ed35c5}
      .world-map-cloud-radar-dot.is-ego-motion{background:#c9d4db;box-shadow:0 0 0 4px #c9d4db66,0 0 16px 5px #c9d4db}
      .world-map-cloud-scale{position:absolute;z-index:3;bottom:16px;left:16px;width:72px;border-top:2px solid #d7eaf4;color:#d7eaf4;text-align:center;font:12px ui-monospace,monospace}
      .world-map-cloud-scale[hidden]{display:none}
      .world-map-cloud-fetch{position:absolute;z-index:4;right:12px;bottom:12px;padding:7px 10px;border:1px solid #9f493c;border-radius:4px;background:#351510ed;color:#ffd6cc;font:12px ui-sans-serif,system-ui,sans-serif}
      .world-map-status-bar .world-map-cloud-fetch{position:static;z-index:auto;order:8;flex-basis:100%;padding:7px 10px}
      .world-map-cloud-side{display:flex;min-width:0;flex-direction:column;gap:12px;padding:16px;border:1px solid var(--wm-border);border-radius:8px;background:var(--wm-surface);color:var(--wm-text);font:14px ui-sans-serif,system-ui,sans-serif}
      .world-map-cloud-side>strong{padding-bottom:8px;border-bottom:1px solid var(--wm-border);font-size:14px}
      .world-map-cloud-side label{display:flex;align-items:center;gap:8px;min-height:30px;color:var(--wm-muted)}
      .world-map-cloud-side input{accent-color:#00d6df}
      .world-map-depth-legend{display:grid;gap:6px}
      .world-map-depth-legend>i{height:12px;border-radius:2px;background:linear-gradient(90deg,#f05a28,#f9c932,#72d055,#1fa4b2,#4663d8,#30123b)}
      .world-map-depth-legend>div{display:flex;justify-content:space-between;color:var(--wm-muted);font-size:12px}
      .world-map-cloud-side small{color:var(--wm-muted);font-size:12px}
      .world-map-cloud-side .world-map-depth-calibration{display:grid;gap:8px;padding-top:10px;border-top:1px solid var(--wm-border)}
      .world-map-cloud-side .world-map-depth-calibration button{justify-self:start;padding:8px 10px;border:1px solid #126d76;border-radius:6px;background:#102b36;color:#bdf9f3;cursor:pointer;font:12px ui-sans-serif,system-ui,sans-serif}
      .world-map-cloud-side .world-map-depth-calibration button:disabled{cursor:wait;opacity:.65}
      .world-map-cloud-axis{display:flex;gap:10px;margin-top:auto;padding-top:10px;border-top:1px solid var(--wm-border);color:#9cdce1;font:12px ui-monospace,monospace}
      @media(max-width:1100px){.world-map-sensor-cloud-layout{grid-template-columns:minmax(0,1fr)}.world-map-cloud-side{display:grid;grid-template-columns:repeat(2,minmax(0,1fr))}.world-map-cloud-side>strong,.world-map-cloud-axis{grid-column:1/-1}}
      @media(max-width:900px){.world-map-cloud-hud,.world-map-cloud-controls{position:static;max-width:none;padding:6px;background:#05070d}.world-map-cloud-controls{justify-content:flex-start}.world-map-cloud-hud{padding-top:8px}.world-map-cloud-side{grid-template-columns:minmax(0,1fr)}}
      .world-map-live-readouts{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,340px),1fr));gap:12px;margin-top:14px}
      .sensor-readout-card{min-width:0;padding:14px;border:1px solid #d7e1da;background:#f7faf8;color:#1c2b22}
      .sensor-readout-card header{display:flex;align-items:center;justify-content:space-between;gap:10px;padding-bottom:9px;border-bottom:1px solid #d7e1da}
      .sensor-readout-card header strong{font:650 12px ui-monospace,monospace;color:#1b4734}
      .sensor-readout-card header small{font:10px ui-monospace,monospace;color:#5a7063;text-align:right}
      .sensor-readout-wide{grid-column:1/-1}
      #world-map-radar-plot{display:block;width:100%;height:145px;margin-top:8px;background:#07120f;border:1px solid #203b2d}
      .sensor-target-list{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:0 16px;color:#40574a;font:11px ui-monospace,monospace}
      .sensor-target-row{display:flex;justify-content:space-between;gap:12px;padding:8px 2px;border-top:1px solid #d7e1da}
      .sensor-readout-values{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:10px 16px;padding:12px 0}
      .sensor-readout-values span{min-width:0;color:#63766b;font-size:10px}
      .sensor-readout-values b{display:block;margin-top:4px;color:#183d2d;font:600 12px ui-monospace,monospace;overflow-wrap:anywhere}
      .sensor-gps-signals{display:flex;align-items:flex-end;gap:8px;min-height:94px;overflow:auto;padding:8px 0 2px;border-top:1px solid #d7e1da}
      .sensor-gps-bar{flex:0 0 34px;display:flex;flex-direction:column;align-items:center;justify-content:flex-end;gap:4px;height:80px;color:#40574a;font:9px ui-monospace,monospace}
      .sensor-gps-bar i{display:block;width:15px;min-height:3px;border-radius:2px 2px 0 0}
      .sensor-distance{display:grid;gap:6px;padding:18px 0 8px}
      .sensor-distance b{font:650 30px ui-monospace,monospace;color:#183d2d}
      .sensor-distance span,.sensor-readout-note{color:#64776c;font-size:10px;line-height:1.5}
      .sensor-readout-note{margin:0}
      .system-instrument-grid{display:grid;grid-template-columns:repeat(5,minmax(112px,1fr));gap:12px;padding:14px 0}
      .system-instrument{display:flex;min-width:0;flex-direction:column;align-items:center;gap:8px;padding:12px 8px 10px;border:1px solid #d7e1da;background:#fff}
      .system-instrument-label{color:#526b5d;font:650 9px ui-monospace,monospace;letter-spacing:.08em}
      .system-gauge{--gauge-value:0;--gauge-color:#16855d;display:grid;width:92px;aspect-ratio:1;place-items:center;border-radius:50%;background:conic-gradient(from -90deg,var(--gauge-color) calc(var(--gauge-value)*1%),#e2eae5 0);position:relative}
      .system-gauge::before{position:absolute;inset:6px;border-radius:50%;background:#fff;content:""}
      .system-gauge-center{z-index:1;display:flex;align-items:baseline;gap:3px;color:#183d2d;font-family:ui-monospace,monospace}
      .system-gauge-center strong{font-size:21px;font-weight:700;font-variant-numeric:tabular-nums}
      .system-gauge-center small{color:#63766b;font-size:10px}
      .system-gauge-temp{--gauge-color:#d58b32}
      .system-gauge-power{--gauge-color:#1787a0}
      .system-instrument-foot{min-height:24px;color:#63766b;font:9px/1.35 ui-monospace,monospace;text-align:center}
      .system-telemetry-strip{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));border-top:1px solid #d7e1da;border-bottom:1px solid #d7e1da}
      .system-telemetry-strip>div{display:grid;gap:5px;min-width:0;padding:10px 12px;border-right:1px solid #d7e1da}
      .system-telemetry-strip>div:last-child{border-right:0}
      .system-telemetry-strip span{color:#63766b;font-size:9px}
      .system-telemetry-strip strong{color:#183d2d;font:650 11px ui-monospace,monospace;overflow-wrap:anywhere}
      .sensor-range-channels span{padding:8px;border:1px solid #d7e1da;background:#fff}
      #worldmodel-live-sensor-panels .map-panel{margin-bottom:14px}
      #worldmodel-live-sensor-panels .map-layout{min-height:0}
      #worldmodel-live-sensor-panels .map-intro{max-width:100ch;line-height:1.55}
      .world-map-sensor-view{--wm-gap:16px;--wm-section-gap:24px;container-type:inline-size;margin-top:12px}
      body.worldmodel-sensors-active .simulation-actions,
      body.worldmodel-sensors-active #view-worldmodel #wm-simulation-toggle,
      body.worldmodel-sensors-active #view-worldmodel .map-panel .panel-head>button[onclick="expandMap()"]{display:none!important}
      body.worldmodel-sensors-active #view-worldmodel>.stats,body.worldmodel-sensors-active #goal-success{display:none!important}
      @media(max-width:760px){.system-instrument-grid{grid-template-columns:repeat(2,minmax(0,1fr))}.system-telemetry-strip{grid-template-columns:repeat(2,minmax(0,1fr))}.system-telemetry-strip>div:nth-child(2){border-right:0}.system-telemetry-strip>div:nth-child(-n+2){border-bottom:1px solid #d7e1da}}
      @container (max-width:760px){.world-map-sensor-2d,.world-map-analysis-grid,.world-map-live-readouts{grid-template-columns:minmax(0,1fr)}.world-map-analysis-grid{grid-template-columns:minmax(0,1fr)}.world-map-depth img{max-height:320px}}
      @media(max-width:700px){.world-map-sensor-2d,.world-map-analysis-grid,.world-map-live-readouts{grid-template-columns:minmax(0,1fr)}.world-map-depth img{max-height:320px}.world-map-controls{gap:7px}}
      body.worldmodel-sensors-active,body.worldmodel-sensors-active #view-worldmodel,body.worldmodel-sensors-active #worldmodel-live-sensor-panels,body.worldmodel-sensors-active #view-worldmodel .shell{background:#05070d!important;color:#e2edf5!important}
      body.worldmodel-sensors-active #page-title,body.worldmodel-sensors-active #page-description,body.worldmodel-sensors-active #view-worldmodel h2,body.worldmodel-sensors-active #view-worldmodel .map-intro,body.worldmodel-sensors-active header.topbar .eyebrow{color:#e2edf5!important}
      body.worldmodel-sensors-active #page-description,body.worldmodel-sensors-active #view-worldmodel .map-intro,body.worldmodel-sensors-active header.topbar .eyebrow{color:#a9b9c8!important}
      body.worldmodel-sensors-active #view-worldmodel #worldmodel-subtabs{border-color:#263b50!important}
      body.worldmodel-sensors-active #view-worldmodel #worldmodel-subtabs button{color:#a9b9c8!important}
      body.worldmodel-sensors-active #view-worldmodel #worldmodel-subtabs button.active,body.worldmodel-sensors-active #view-worldmodel #worldmodel-subtabs button[aria-selected="true"]{color:#00d6df!important}
      body.worldmodel-sensors-active #view-worldmodel .world-map-status-bar{top:0}
      body.worldmodel-sensors-active .world-map-sensor-metrics{flex:1 1 100%;width:100%;max-width:100%;flex-wrap:wrap;gap:6px 16px;padding:8px 0 0;margin-left:0;overflow:visible;border-top:1px solid #263b50}
      body.worldmodel-sensors-active .world-map-sensor-metrics span{display:flex;flex:1 1 160px;min-width:130px;gap:4px;padding:0;border:0;background:transparent;color:#9aafc0;font-size:11px;white-space:nowrap}
      body.worldmodel-sensors-active .world-map-sensor-metrics span:has(#world-map-frame-state){display:none}
      body.worldmodel-sensors-active .world-map-sensor-metrics b{max-width:min(220px,55vw);overflow:hidden;color:#e2edf5;text-overflow:ellipsis;white-space:nowrap}
      body.worldmodel-sensors-active .world-map-sensor-metrics b[data-state="offline"]{color:#ff7373!important}
      body.worldmodel-sensors-active .world-map-sensor-metrics b[data-state="stale"]{color:#ffb547!important}
      body.worldmodel-sensors-active .world-map-sensor-metrics b[data-state="live"]{color:#39e59a!important}
      body.worldmodel-sensors-active .sensor-readout-card:has(.sensor-state-chip[data-state="stale"]) .sensor-readout-values,body.worldmodel-sensors-active .sensor-readout-card:has(.sensor-state-chip[data-state="stale"]) canvas{opacity:.55}
      body.worldmodel-sensors-active .world-map-live-readouts{grid-template-columns:repeat(auto-fit,minmax(min(100%,300px),1fr))}
      body.worldmodel-sensors-active .system-gauge-center strong{font-size:15px!important}
      body.worldmodel-sensors-active .system-gauge{width:88px}
      body.worldmodel-sensors-active .system-gauge::after{right:-15px}
      body.worldmodel-sensors-active .sensor-readout-values b{overflow-wrap:normal;white-space:nowrap}
      body.worldmodel-sensors-active #world-map-gps-signals{overflow:hidden;scrollbar-width:none}
      body.worldmodel-sensors-active #world-map-gps-signals::-webkit-scrollbar{display:none}
      body.worldmodel-sensors-active #view-worldmodel>.stats,body.worldmodel-sensors-active #goal-success{display:none!important}
      body.worldmodel-sensors-active #view-worldmodel .shell{max-width:1680px;padding:76px 24px 24px}
      .world-map-sensor-view{--wm-bg:#05070d;--wm-surface:#0a0f1a;--wm-raised:#101b29;--wm-border:#263b50;--wm-text:#e2edf5;--wm-muted:#9aafc0;--wm-cyan:#00d6df;--wm-magenta:#ed35c5;color:var(--wm-text);margin-top:8px}
      .world-map-status-bar{position:sticky;top:0;z-index:8;scroll-margin-top:76px;display:flex;align-items:center;gap:clamp(14px,2.5vw,36px);flex-wrap:wrap;padding:10px 16px;margin:0 -2px 14px;border:1px solid var(--wm-border);border-radius:8px;background:rgba(5,7,13,.98);box-shadow:0 6px 18px #02060a44}
      .world-map-status-bar>span{display:grid;gap:3px;color:var(--wm-muted);font:12px/1.2 ui-sans-serif,system-ui,sans-serif}
      .world-map-status-bar b{color:var(--wm-text);font:600 14px/1.2 ui-monospace,monospace;font-variant-numeric:tabular-nums}
      [data-state="live"], [data-state="ready"]{color:#39e59a!important}[data-state="stale"]{color:#ffb547!important}[data-state="offline"]{color:#91a0ad!important}[data-state="loading"]{color:#68cfe0!important}
      .world-map-sensor-metrics{gap:8px;padding:8px 0 12px;color:var(--wm-muted);font:12px ui-monospace,monospace}
      .world-map-sensor-metrics span{padding:6px 9px;border:1px solid var(--wm-border);border-radius:6px;background:var(--wm-surface);color:var(--wm-muted)}
      .world-map-sensor-metrics b{color:var(--wm-text)}
      .world-map-sensor-2d{grid-template-columns:repeat(2,minmax(0,1fr));gap:var(--wm-gap);align-items:stretch}
      .world-map-camera,.world-map-depth,.world-map-odometry-view,.world-map-segmentation-panel,.sensor-readout-card,.system-instrument{border:1px solid var(--wm-border);border-radius:8px;background:var(--wm-surface);color:var(--wm-text)}
      .world-map-camera,.world-map-depth,.world-map-odometry-view,.world-map-segmentation-panel{display:flex;flex-direction:column;min-width:0;aspect-ratio:4/3;overflow:hidden}
      .world-map-sensor-heading,.sensor-readout-card header{min-height:42px;padding:10px 12px;border-bottom:1px solid var(--wm-border);background:var(--wm-raised);color:var(--wm-cyan);font:600 12px/1.25 ui-sans-serif,system-ui,sans-serif}
      .world-map-sensor-heading small,.sensor-readout-card header small{color:var(--wm-muted);font:12px ui-monospace,monospace}
      .world-map-image-wrap,.world-map-segmentation-preview{width:100%;flex:1;aspect-ratio:auto;max-height:none;min-height:0;background:#02060a}
      .world-map-image-wrap img{object-fit:contain}
      .world-map-depth img{width:100%;height:0;flex:1;min-height:0;max-height:none;aspect-ratio:auto;object-fit:cover;background:#02060a}
      .world-map-depth-calibration{margin-top:auto;border-top:1px solid var(--wm-border)}
      .world-map-depth-calibration small,.world-map-odometry-footnote,.world-map-empty,.world-map-sensor-note{color:var(--wm-muted);font:12px/1.45 ui-sans-serif,system-ui,sans-serif}
      .world-map-depth-calibration button{border-color:#126d76;border-radius:6px;background:#102b36;color:#bdf9f3}
      .world-map-segmentation-panel{margin:0}
      .world-map-segmentation-preview{display:grid;flex:1}
      #world-map-segmentation-overlay{width:100%;height:100%;object-fit:cover}
      .world-map-segmentation-classes{gap:8px 14px;padding:10px 12px;color:var(--wm-muted);font:12px/1.5 ui-sans-serif,system-ui,sans-serif;border-top:1px solid var(--wm-border)}
      .world-map-vision-footer{grid-column:1/-1;padding:10px 12px;border-top:1px solid var(--wm-border);background:var(--wm-surface)}
      .world-map-vision-footer{margin-top:12px}
      .world-map-odometry-view{justify-content:flex-start}
      .odom-plot{position:relative;flex:1;min-height:0;background:#050b12}
      #world-map-odometry-map{display:block;width:100%;height:100%;background:#050b12}
      .odom-edge-label,.odom-position-label{position:absolute;z-index:1;color:#a9c2d0;font:12px ui-monospace,monospace;pointer-events:none}
      .odom-forward{top:8px;left:50%;transform:translateX(-50%)}
      .odom-lateral{bottom:8px;left:50%;transform:translateX(-50%)}
      .odom-position-label{top:8px;right:10px;padding:5px 7px;border-radius:4px;background:#0a0f1ae8;color:#00e2dd;font-size:12px;white-space:nowrap}
      .world-map-odometry-footnote{padding:8px 12px 10px;color:var(--wm-muted);font:12px/1.4 ui-sans-serif,system-ui,sans-serif}
      .world-map-live-readouts{grid-template-columns:repeat(auto-fit,minmax(min(100%,300px),1fr));gap:var(--wm-gap);margin-top:var(--wm-section-gap);align-items:stretch}
      .world-map-compute-card{margin-top:var(--wm-section-gap)}
      .sensor-readout-card{display:flex;min-width:0;min-height:100%;flex-direction:column;padding:0 12px 12px}
      .sensor-readout-card[hidden],.world-map-offline-pill[hidden]{display:none!important}
      .sensor-readout-card header{display:grid;grid-template-columns:minmax(0,1fr) auto;align-items:center;gap:10px;margin:0 -12px 8px;padding:8px 12px}
      .sensor-heading-copy{display:grid;min-width:0;gap:2px}
      .sensor-readout-card header strong{overflow:hidden;color:var(--wm-text);font:600 14px/1.25 ui-sans-serif,system-ui,sans-serif;text-overflow:ellipsis;white-space:nowrap}
      .sensor-card-source{overflow:hidden;color:var(--wm-muted);font:12px/1.3 ui-sans-serif,system-ui,sans-serif;text-overflow:ellipsis;white-space:nowrap}
      .sensor-readout-card header .sensor-state-chip{max-width:140px;overflow:hidden;padding:4px 7px;border:1px solid var(--wm-border);border-radius:999px;background:#0a0f1a;font:12px/1.2 ui-sans-serif,system-ui,sans-serif;text-overflow:ellipsis;white-space:nowrap}
      #world-map-radar-plot{display:block;width:100%;height:auto;min-height:160px;flex:1;aspect-ratio:2/1;background:#050b12;border:1px solid var(--wm-border);border-radius:5px}
      .sensor-target-list{grid-template-columns:1fr;color:var(--wm-text);font:12px ui-monospace,monospace}
      .sensor-target-row{border-color:var(--wm-border)}
      .sensor-readout-values span,.sensor-distance span,.sensor-readout-note{color:var(--wm-muted);font-size:12px;line-height:1.45}
      .sensor-readout-values b{color:var(--wm-text);font:600 13px ui-monospace,monospace;white-space:nowrap}
      .sensor-readout-values span{display:grid;gap:4px;align-content:start}
      .sensor-gps-signals{display:grid;grid-template-columns:repeat(auto-fill,minmax(38px,1fr));align-items:end;gap:6px;min-height:100px;overflow:hidden;border-color:var(--wm-border)}
      .sensor-gps-bar{width:auto;height:84px;color:var(--wm-muted);font:12px ui-monospace,monospace}
      .sensor-gps-bar small{font-size:12px}
      .sensor-gps-more{align-self:center;justify-self:center;color:var(--wm-muted);font:12px ui-sans-serif,system-ui,sans-serif}
      .sensor-distance b{color:var(--wm-text);font-size:26px}
      .world-map-offline-strip{display:flex;align-items:center;gap:8px 14px;flex-wrap:wrap;margin-top:10px;padding:10px 12px;border:1px solid var(--wm-border);border-radius:8px;background:var(--wm-surface);color:var(--wm-muted);font:12px ui-sans-serif,system-ui,sans-serif}
      .world-map-offline-strip>strong{color:#91a0ad;font-size:12px}
      .world-map-offline-pill{display:inline-flex;align-items:center;gap:7px;padding:5px 8px;border:1px solid var(--wm-border);border-radius:5px;background:#080f17}
      .world-map-offline-pill b{color:var(--wm-text)}.world-map-offline-pill>span{color:var(--wm-muted)}
      .system-instrument-grid{grid-template-columns:repeat(5,minmax(0,1fr));gap:10px;padding:12px 0}
      .system-instrument{display:flex;flex-direction:column;align-items:center;justify-content:center;gap:8px;padding:12px 10px}
      .system-instrument-label{color:var(--wm-muted);font:600 12px ui-sans-serif,system-ui,sans-serif;text-align:center}
      .system-gauge{position:relative;width:88px;flex:none;background:conic-gradient(from -90deg,var(--gauge-color) calc(var(--gauge-value)*1%),#253544 0)}
      .system-gauge::before{inset:7px;background:var(--wm-surface)}
      .system-gauge::after{position:absolute;right:-17px;top:50%;transform:translateY(-50%);color:var(--wm-muted);font:12px ui-sans-serif,system-ui,sans-serif}
      #world-map-cpu-gauge::after,#world-map-memory-gauge::after{content:"%"}
      #world-map-cpu-temp-gauge::after,#world-map-gpu-temp-gauge::after{content:"\xB0C"}
      #world-map-power-gauge::after{content:"W"}
      .system-gauge-center{align-items:center;justify-content:center;gap:0;color:var(--wm-text)}
      .system-gauge-center strong{font-size:16px}.system-gauge-center small{display:none}
      .system-instrument-foot{min-height:0;color:var(--wm-muted);font:12px/1.35 ui-sans-serif,system-ui,sans-serif;text-align:center}
      .imu-attitude{display:flex;align-items:center;justify-content:center;gap:12px;padding:10px 0;border-bottom:1px solid var(--wm-border)}
      .imu-attitude-disc{position:relative;width:72px;aspect-ratio:1;overflow:hidden;flex:none;border:2px solid var(--wm-cyan);border-radius:50%;background:#10243a}
      .imu-attitude-horizon{position:absolute;left:-30%;top:-55%;width:160%;height:210%;transform:translateY(var(--imu-pitch,0px)) rotate(var(--imu-roll,0deg));background:linear-gradient(to bottom,#1747a3 0 50%,#69432f 50% 100%)}
      .imu-attitude-horizon span{position:absolute;left:0;right:0;top:50%;height:2px;background:#e0bc78}
      .imu-attitude-mark{position:absolute;left:50%;top:50%;width:25px;height:2px;transform:translate(-50%,-50%);background:#f3f7fb;box-shadow:0 0 0 2px #0b1420}
      .imu-attitude b{display:block;color:var(--wm-muted);font:600 12px ui-sans-serif,system-ui,sans-serif}
      .imu-attitude small{display:block;color:var(--wm-muted);font:12px/1.4 ui-sans-serif,system-ui,sans-serif}
      .system-telemetry-strip{border-color:var(--wm-border)}
      .system-telemetry-strip>div{border-color:var(--wm-border)}
      .system-telemetry-strip span{color:var(--wm-muted);font-size:12px}
      .system-telemetry-strip strong{color:var(--wm-text);font:600 13px ui-monospace,monospace}
      #world-map-system-note{padding:8px 0 0;color:#c3d2dc;font-size:12px}
      .sensor-range-channels span{border-color:var(--wm-border);background:#080f17}
      .world-map-calibration-guide{width:min(880px,calc(100vw - 32px));max-height:min(92vh,1000px);padding:0;border:1px solid #263b50;border-radius:8px;background:#0a0f1a;color:#e2edf5;box-shadow:0 24px 80px #000b}
      .world-map-calibration-guide::backdrop{background:#02060acc;backdrop-filter:blur(3px)}
      .world-map-calibration-guide__surface{display:grid;gap:14px;padding:20px;overflow:auto;max-height:min(92vh,1000px);font:14px/1.45 ui-sans-serif,system-ui,sans-serif}
      .world-map-calibration-guide header{display:flex;align-items:center;justify-content:space-between;gap:16px;padding-bottom:12px;border-bottom:1px solid #263b50}
      .world-map-calibration-guide h2{margin:0;color:#e2edf5;font-size:22px;line-height:1.2}
      .world-map-calibration-kicker{margin:0 0 5px;color:#00d6df;font-size:12px;font-weight:650}
      .world-map-calibration-close{width:36px;height:36px;border:1px solid #344a5e;border-radius:6px;background:#101b29;color:#e2edf5;font-size:22px;cursor:pointer}
      .world-map-calibration-intro{margin:0;color:#c3d2dc}
      .world-map-calibration-target{display:grid;gap:6px;padding:10px 12px;border:1px solid #087d86;border-radius:5px;background:#0b1a22;color:#e2edf5;font-weight:600}
      .world-map-calibration-target select{width:100%;min-height:38px;padding:7px 9px;border:1px solid #344a5e;border-radius:4px;background:#080e17;color:#e2edf5;font:14px ui-sans-serif,system-ui,sans-serif}
      .world-map-calibration-target small{color:#a9b9c8;font-size:12px;font-weight:400}
      .world-map-calibration-stages{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:8px 18px;margin:0;padding-left:24px}
      .world-map-calibration-stages li{padding:8px 10px;border-left:2px solid #263b50;background:#080e17}
      .world-map-calibration-stages li:nth-child(6){border-color:#00d6df;background:#0b1a22}
      .world-map-calibration-stages b,.world-map-calibration-stages span{display:block}
      .world-map-calibration-stages b{margin-bottom:3px;color:#e2edf5;font-size:14px}
      .world-map-calibration-stages span{color:#a9b9c8;font-size:12px}
      .world-map-calibration-checks{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:8px}
      .world-map-calibration-checks label{display:flex;align-items:flex-start;gap:8px;padding:8px 10px;border:1px solid #263b50;border-radius:5px;color:#c3d2dc;font-size:12px}
      .world-map-calibration-checks input{margin-top:2px;accent-color:#00d6df}
      .world-map-calibration-caution{margin:0;padding:10px 12px;border-left:3px solid #ffb547;background:#201a0e;color:#f0d7a6;font-size:12px}
      .world-map-calibration-progress{min-height:20px;margin:0;color:#9aafc0;font:12px ui-monospace,monospace}
      .world-map-calibration-guide footer{display:flex;justify-content:flex-end;gap:8px;padding-top:12px;border-top:1px solid #263b50}
      .world-map-calibration-guide footer button{padding:9px 13px;border:1px solid #344a5e;border-radius:5px;background:#101b29;color:#e2edf5;font:600 14px ui-sans-serif,system-ui,sans-serif;cursor:pointer}
      .world-map-calibration-guide footer .primary{border-color:#087d86;background:#07535d;color:#e8ffff}
      @media(max-width:680px){.world-map-calibration-stages,.world-map-calibration-checks{grid-template-columns:minmax(0,1fr)}.world-map-calibration-guide__surface{padding:14px}}
      @media(max-width:980px){.world-map-live-readouts{grid-template-columns:repeat(2,minmax(0,1fr))}.system-instrument-grid{grid-template-columns:repeat(3,minmax(0,1fr))}}
      @media(max-width:640px){.world-map-sensor-2d,.world-map-live-readouts{grid-template-columns:minmax(0,1fr)}.world-map-status-bar{position:static;gap:12px}.system-instrument-grid{grid-template-columns:repeat(2,minmax(0,1fr))}.system-telemetry-strip{grid-template-columns:repeat(2,minmax(0,1fr))}.world-map-controls{gap:7px}}
    `,document.head.append(v)}}var Po=(i,e=1)=>new is({color:i,roughness:.82,metalness:.02,transparent:e<1,opacity:e}),zu={target:"#efa678",chair:"#83b3d5",table:"#d3bd67",obstacle:"#a77ba5",mobile_obstacle:"#db83bf",object:"#a9c4b2"};function Ku(i,e="#07120f"){if(!i)return null;let t;try{t=new Co({antialias:!0,alpha:!1,powerPreference:"low-power"})}catch(d){return i.textContent=`3D rendering unavailable: ${d.message}`,null}t.setPixelRatio(Math.min(window.devicePixelRatio||1,1.5)),t.setClearColor(e,1),i.prepend(t.domElement);let n=new Zr;n.background=new Ne(e);let r=new Dt(42,1,.05,200);n.add(new as("#d7f4e4","#14231c",2));let s=new ls("#e4fff0",2.2);s.position.set(-4,10,6),n.add(s);let a=()=>{let d=Math.max(1,i.clientWidth),u=Math.max(1,i.clientHeight);t.setSize(d,u,!1),r.aspect=d/u,r.updateProjectionMatrix()},o=new ResizeObserver(a);o.observe(i),a();let l=null;i.addEventListener("contextmenu",d=>d.preventDefault()),i.addEventListener("pointerdown",d=>{l={x:d.clientX,y:d.clientY,pan:d.button===2||d.shiftKey},r.userData.userAdjusted=!0,i.setPointerCapture(d.pointerId)}),i.addEventListener("pointermove",d=>{if(!l)return;let u=d.clientX-l.x,h=d.clientY-l.y;l.x=d.clientX,l.y=d.clientY;let p=r.userData.target||new N;if(l.pan){let g=r.position.distanceTo(p)*.0018,x=new N().setFromMatrixColumn(r.matrix,0),m=new N().setFromMatrixColumn(r.matrix,1),f=x.multiplyScalar(-u*g).add(m.multiplyScalar(h*g));r.position.add(f),p.add(f),r.userData.target=p}else{let g=new cs().setFromVector3(r.position.clone().sub(p));g.theta-=u*.006,g.phi=yt.clamp(g.phi+h*.006,.12,Math.PI-.12),r.position.copy(new N().setFromSpherical(g).add(p))}r.lookAt(p),c()}),i.addEventListener("pointerup",()=>{l=null}),i.addEventListener("pointercancel",()=>{l=null}),i.addEventListener("wheel",d=>{d.preventDefault(),r.userData.userAdjusted=!0;let u=r.userData.target||new N,h=r.position.clone().sub(u);h.multiplyScalar(yt.clamp(1+d.deltaY*.001,.82,1.2)),r.position.copy(u).add(h),c()},{passive:!1});let c=()=>t.render(n,r);return{renderer:t,scene:n,camera:r,render:c,resize:a,observer:o}}var Dn=Ku(j("world-map-sim-3d")),sn,ku="",ue=Ku(j("world-map-sensor-3d-viewport"),"#05070d"),tt=null,fi=null,Hu="",Ar="",Sc=!1,$t=null,Ec=0,ju="",Vu="",Ui=new Bt,Oi=new Bt,Lo=null,Fo=null,Gu="",vs=new Bt,Ms=new Bt;if(ue){let i=[],e=[];for(let s=-10;s<=10;s+=1){let a=new Ne(s%5===0?"#426078":"#23394a");i.push(s,0,1,s,0,-15,-10,0,-4+s,10,0,-4+s);for(let o=0;o<4;o+=1)e.push(a.r,a.g,a.b)}let t=new dt;t.setAttribute("position",new je(i,3)),t.setAttribute("color",new je(e,3)),Ui.add(new oi(t,new nn({vertexColors:!0,transparent:!0,opacity:.78}))),Lo=new Wn(new dt().setFromPoints([new N(0,0,0),new N(0,.18,0)]),new nn({color:"#9aafc0",transparent:!0,opacity:.8})),Ui.add(Lo),Fo=new st(new li(.022,12,8),new Xt({color:"#62f1c1"})),Ui.add(Fo),Oi.add(new st(new li(.025,16,10),new Xt({color:"#f4f7ff"})));let n=(s,a)=>{let o=new N(...s).normalize();Oi.add(new us(o,new N,.2,a,.045,.028))};n([1,0,0],"#ef6a73"),n([0,1,0],"#62d994"),n([0,0,-1],"#66a8ff");let r=new dt().setFromPoints([new N(-.5,.03,-2),new N(.5,.03,-2)]);Ui.add(new Wn(r,new nn({color:"#d7eaf4"}))),ue.scene.add(Ui,Oi,vs,Ms)}var gt=j("world-map-sensor-3d-viewport");gt?.querySelector(".world-map-cloud-axis span:last-child")?.replaceChildren("Z\u2212 \xB7 forward");var Uo=gt?.querySelector(".world-map-cloud-labels"),Tc=0,Wu=performance.now();if(ue){let i=ue.render,e=0;ue.render=()=>{i(),Tc+=1,xh();let t=performance.now();t-e>=500&&(Zn(),e=t)},gt?.querySelector('[data-cloud-action="reset"]')?.addEventListener("click",()=>{gt.classList.remove("is-camera-view"),ue.camera.fov=42,ue.camera.userData.userAdjusted=!1,Sc=!1,ue.resize(),Zn(),zi(),Es(),Go()}),gt?.querySelectorAll("[data-cloud-view]").forEach(t=>t.addEventListener("click",()=>wx(t.dataset.cloudView))),gt?.querySelectorAll("[data-cloud-layer]").forEach(t=>t.addEventListener("change",()=>{let n=t.dataset.cloudLayer;n==="cloud"&&tt&&(tt.visible=t.checked),n==="detections"&&(fi&&(fi.visible=t.checked),t.checked&&at&&Wo(at,Ss)),n==="radar"&&zi(Sn,!0),n==="odometry"&&(Ms.visible=t.checked),ue.render()})),j("world-map-cloud-point-size")?.addEventListener("input",t=>{tt&&(tt.material.uniforms.uPointSize.value=Number(t.target.value)/1e3),ue.render()})}var Xu=0;function Qu(i){document.visibilityState!=="hidden"&&ut==="sensors"&&Rt==="3d"&&ue&&i-Xu>=1e3/24&&(Xu=i,ue.render()),requestAnimationFrame(Qu)}requestAnimationFrame(Qu);var ut=window.bodyWorldModelView==="sensors"?"sensors":"simulation",Rt="2d",Bi=null,gc=!1,xc=!1;function nx(i,e,t){let n=new st(new Ei(e,t),Po("#0d1b15"));n.rotation.x=-Math.PI/2,n.position.y=-.03,i.add(n);let r=new ds(Math.max(e,t),Math.ceil(Math.max(e,t)*2),"#4e8d69","#294c3a");r.position.y=.005,i.add(r);let s=new oi(new ns(new wn(e,.08,t)),new nn({color:"#70b28a",transparent:!0,opacity:.72}));s.position.y=.01,i.add(s)}function ix(i){let e=String(i.kind||"object").toLowerCase(),t=Math.max(.25,Math.min(2.2,Number(i.size)||.6));return e.includes("chair")?new wn(t*1.15,.8,t*1.05):e.includes("table")?new wn(t*1.6,.72,t*1.4):e.includes("obstacle")?new Rn(t*.52,t*.62,1.15,18):e==="target"||e.includes("cup")?new Rn(t*.34,t*.42,.48,18):new wn(t,Math.max(.35,t),t)}function _c(i,e="#d8eee1"){let t=document.createElement("canvas");t.width=512,t.height=96;let n=t.getContext("2d");n.font="600 42px ui-monospace, monospace",n.textAlign="center",n.textBaseline="middle",n.fillStyle="#06100de8",n.fillRect(0,10,t.width,t.height-20),n.fillStyle=e,n.fillText(String(i).slice(0,32),t.width/2,t.height/2);let r=new Qr(t);r.colorSpace=Nt;let s=new Kr(new fr({map:r,transparent:!0,depthTest:!1}));return s.scale.set(1.65,.31,1),s}function Ho(i){if(!Dn)return;let e=i?.perception||{},t=i?.sim||{},n=i?.mode==="sim",r=Object.entries(t.objects||{}).map(([y,C])=>({id:y,label:y.replaceAll("_"," "),kind:C.kind,position:[C.x,C.y,0],size:y==="cup"?.4:.8})),s=n?r:Array.isArray(e.objects)?e.objects:r,a=n?t.body||[0,0,0]:e.body?.position||t.body||[0,0,0],o=Math.max(2,Number(t.width)||12),l=Math.max(2,Number(t.height)||12),c=t.shelf||[1,9],d=n?Number(t.heading_deg||0)*Math.PI/180:Number(e.body?.orientation||0),u=JSON.stringify([o,l,c,a,d,s.map(y=>[y.id,y.kind,y.position,y.size])]);if(u===ku)return;ku=u,sn&&(Dn.scene.remove(sn),sn.traverse(y=>{y.geometry?.dispose(),Array.isArray(y.material)?y.material.forEach(C=>C.dispose()):y.material?.dispose()})),sn=new Bt,nx(sn,o,l);let h=new st(new Rn(.48,.48,.035,32),new Xt({color:"#79d8a0",transparent:!0,opacity:.32}));h.position.set(Number(c[0])-o/2,.02,-(Number(c[1])-l/2)),sn.add(h);let p=_c("GOAL","#b9f5ce");p.position.set(h.position.x,.35,h.position.z),sn.add(p);let g=new Bt;g.position.set(Number(a[0])-o/2,0,-(Number(a[1])-l/2));let x=new st(new Rn(.28,.32,.32,24),Po("#8ee5b1"));x.position.y=.2,g.add(x);let m=new st(new mr(.13,.38,16),Po("#d8ffe5"));m.rotation.z=-Math.PI/2,m.position.set(.38,.24,0),g.add(m),g.rotation.y=-d,sn.add(g);let f=_c("BODY","#b6f1d3");f.position.set(g.position.x,.82,g.position.z),sn.add(f);for(let y of s){let C=y.position||[0,0,0],E=String(y.kind||"object").toLowerCase(),R=zu[E]||zu.object,P=new st(ix(y),Po(R,E.includes("mobile")?.92:1)),w=E.includes("obstacle")?.58:E==="table"||E==="chair"?.38:.25;P.position.set(Number(C[0])-o/2,w,-(Number(C[1])-l/2)),sn.add(P);let v=new st(new Rn(.025,.025,.025,10),new Xt({color:R}));v.position.set(P.position.x,.035,P.position.z),sn.add(v);let T=_c(y.label||y.kind||"OBJECT",R);T.position.set(P.position.x,w+.86,P.position.z),sn.add(T)}Dn.scene.add(sn);let S=new N(0,0,0);Dn.camera.userData.target=S;let M=Math.max(o,l)*1.3;Dn.camera.userData.userAdjusted||(Dn.camera.position.set(0,M*.62,M),Dn.camera.lookAt(S)),Dn.render()}function eh(i){ut=i;let e=j("world-map-sensor-view"),t=fn?.querySelector(".map-layout");e&&(e.hidden=i!=="sensors"),t&&(t.hidden=i==="sensors");let n=fn?.querySelector('.panel-head button[onclick="expandMap()"]');n&&(n.hidden=i==="sensors");let r=fn?.querySelector(".panel-head h2");r&&(r.textContent=i==="sensors"?"Live sensor observatory":"Simulation \xB7 world ground truth"),fn?.querySelector(".map-intro")?.replaceChildren(document.createTextNode(i==="sensors"?"Live hardware and perception feeds only. No simulator positions, virtual LiDAR returns or synthetic objects are included.":"Synthetic room, robot pose and object positions for controlled testing. These are simulation ground truth, not live sensor measurements.")),fn?.querySelector(".truth-note")?.toggleAttribute("hidden",i==="sensors"),document.querySelectorAll(".simulation-actions").forEach(s=>{s.hidden=i==="sensors"}),i==="sensors"?Ic():Bi&&Ho(Bi),th()}function rx(i){Rt=i;let e=fn?.querySelector(".map-wrap"),t=j("world-map-sim-3d"),n=j("world-map-sensor-2d"),r=j("world-map-sensor-3d");ut==="simulation"?(e&&(e.hidden=i!=="2d"),t&&(t.hidden=i!=="3d"),e&&e.classList.toggle("is-3d",i==="3d"),Bi&&i==="3d"&&requestAnimationFrame(()=>{Dn?.resize(),Ho(Bi),Dn?.render()})):(n&&(n.hidden=i!=="2d"),r&&(r.hidden=i!=="3d"),i==="3d"&&requestAnimationFrame(()=>{Go(),at&&Wo(at,Ss),ue?.render()})),document.querySelectorAll("[data-render]").forEach(s=>s.setAttribute("aria-pressed",String(s.dataset.render===i))),th()}function th(){let i=j("world-map-state");i&&(i.textContent=`${ut==="simulation"?"Simulation":"Live sensors"} \xB7 ${Rt.toUpperCase()}`);let e=fn?.querySelector(".map-wrap"),t=j("world-map-sim-3d");e&&t&&ut==="simulation"&&(e.hidden=Rt!=="2d",t.hidden=Rt!=="3d")}window.addEventListener("body-worldmodel-viewchange",i=>eh(i.detail?.view==="sensors"?"sensors":"simulation"));window.addEventListener("resize",()=>{ut==="sensors"&&Rt==="3d"&&requestAnimationFrame(Go)});document.querySelectorAll("[data-render]").forEach(i=>i.addEventListener("click",()=>rx(i.dataset.render)));j("world-map-midas-calibrate")?.addEventListener("click",uh);j("world-map-midas-calibrate-3d")?.addEventListener("click",uh);gx();eh(window.bodyWorldModelView==="sensors"?"sensors":"simulation");function sx(i,e,t){let n=j("world-map-yolo-overlay");n.replaceChildren(),n.classList.remove("is-stale"),n.setAttribute("viewBox",`0 0 ${e} ${t}`);for(let r of i||[]){let s=r.bbox;if(!Array.isArray(s)||s.length<4)continue;let[a,o,l,c]=s.map(Number);if(![a,o,l,c].every(Number.isFinite))continue;let d=Number(r.overlayAgeS)>.5||r.overlaySourceStale,u=document.createElementNS("http://www.w3.org/2000/svg","rect");u.setAttribute("x",String(a*e)),u.setAttribute("y",String(o*t)),u.setAttribute("width",String(Math.max(0,l-a)*e)),u.setAttribute("height",String(Math.max(0,c-o)*t)),u.setAttribute("fill","none"),u.setAttribute("stroke",d?"#f2bc65":"#62f1c1"),u.setAttribute("opacity",d?"0.72":"1"),u.setAttribute("stroke-width",String(Math.max(e,t)*.004)),n.append(u);let h=document.createElementNS("http://www.w3.org/2000/svg","text");h.setAttribute("x",String(a*e)),h.setAttribute("y",String(Math.max(16,o*t-5))),h.setAttribute("fill","#dffff1"),h.setAttribute("font-size",String(Math.max(12,e*.026))),h.setAttribute("font-family","ui-monospace, monospace"),h.setAttribute("paint-order","stroke"),h.setAttribute("stroke","#07120f"),h.setAttribute("stroke-width",String(Math.max(2,e*.004)));let p=d?`LAST SEEN ${Math.max(0,Number(r.overlayAgeS)||0).toFixed(1)}s \xB7 `:"";h.textContent=`${p}${r.label||r.class_name||r.class||"object"} ${Math.round(Number(r.confidence||r.score||0)*100)}%`,n.append(h)}}function nh(i){let e=Number(i?.captured_at)>0?Date.now()/1e3-Number(i.captured_at):1/0;return!["ready","stale"].includes(i?.state)||e<0||e>2.5?[]:(i.detections||[]).filter(t=>{let n=Number(t.confidence??t.score??0),r=t.bbox;return n>=.25&&Array.isArray(r)&&r.length>=4&&r.slice(0,4).every(s=>Number.isFinite(Number(s)))})}function ax(i){return String(i.label||i.class_name||i.class||"object").toLowerCase()}function ox(i,e){if(!Array.isArray(i)||!Array.isArray(e))return 0;let[t,n,r,s]=i.map(Number),[a,o,l,c]=e.map(Number),d=Math.max(0,Math.min(r,l)-Math.max(t,a))*Math.max(0,Math.min(s,c)-Math.max(n,o)),u=Math.max(0,r-t)*Math.max(0,s-n),h=Math.max(0,l-a)*Math.max(0,c-o);return d/Math.max(1e-9,u+h-d)}function lx(i){let e=Date.now()/1e3,t=Number(i?.captured_at)||0,n=t>0?e-t:1/0,r=nh(i),s=String(i?.frame_id||t);if(s&&s!==Ou&&r.length&&n>=0&&n<=2.5){Ou=s;let a=new Set(Li.map((o,l)=>l));for(let o of r){let l=ax(o),c=-1,d=.05;for(let h of a){let p=Li[h];if(p.label!==l)continue;let g=ox(p.detection.bbox,o.bbox);g>d&&(d=g,c=h)}let u=c>=0?Li[c]:{id:Q0++,label:l,detection:o,lastSeenAt:t};c>=0&&a.delete(c),u.detection=o,u.lastSeenAt=t,u.sourceStale=i.state!=="ready"||i.paired===!1,c<0&&Li.push(u)}}return Li=Li.filter(a=>e-a.lastSeenAt<=j0),Li.map(a=>({...a.detection,overlayAgeS:e-a.lastSeenAt,overlaySourceStale:a.sourceStale}))}function cx(i){return i?.state!=="ready"||i?.paired===!1?[]:(i.detections||[]).filter(e=>{let t=Number(e.confidence??e.score??0),n=String(e.label||e.class_name||e.class||"");return t>=(/person|human/i.test(n)?.5:.45)})}function ih(i,e,t,n="image/jpeg"){t?(i.src=`data:${n};base64,${t}`,i.hidden=!1,e.hidden=!0):(i.removeAttribute("src"),i.hidden=!0,e.hidden=!1)}async function dx(i){let e=j("world-map-segmentation-overlay"),t=j("world-map-segmentation-classes"),n=j("world-map-segmentation-empty");if(!e||!t||!n)return;let r=i?.mask_png_base64,a=String(i?.frame_id||"")||String(i?.captured_at||"");if(!i?.available||!r){e.hidden=!0,n.hidden=!1,n.textContent=`${i?.state==="disabled"?"Enable SegFormer in Camera settings":`SegFormer ${i?.state||"waiting"}`}${i?.error?` \xB7 ${i.error}`:""}`,t.textContent="No semantic classes available",pc="";return}if(a===pc){e.hidden=!1,n.hidden=!0;return}let o=new Image;o.src=`data:image/png;base64,${r}`;try{await o.decode()}catch{return!1}if(a!==String(Cr?.frame_id||Cr?.captured_at||""))return;let l=document.createElement("canvas");l.width=o.naturalWidth,l.height=o.naturalHeight;let c=l.getContext("2d",{willReadFrequently:!0});c.drawImage(o,0,0);let d=c.getImageData(0,0,l.width,l.height).data;e.width=l.width,e.height=l.height;let u=e.getContext("2d"),h=u.createImageData(e.width,e.height),p=new Map;for(let x=0;x<d.length;x+=4){let m=d[x];if(!p.has(m)){let S=Zu(m).getHexString();p.set(m,[parseInt(S.slice(0,2),16),parseInt(S.slice(2,4),16),parseInt(S.slice(4,6),16)])}let f=p.get(m);h.data[x]=f[0],h.data[x+1]=f[1],h.data[x+2]=f[2],h.data[x+3]=d[x+3]}u.putImageData(h,0,0),e.hidden=!1,n.hidden=!0,pc=a;let g=(i.classes||[]).slice(0,7).map(x=>{let m=document.createElement("span"),f=document.createElement("i");return f.style.backgroundColor=`#${Zu(x.id).getHexString()}`,m.append(f,`${x.label} ${Math.round(Number(x.ratio||0)*100)}%`),m});t.replaceChildren(...g),g.length||(t.textContent="Mask available")}function ux(i,e=Ht){if(!e?.available)return i;let t=Number(e.inverse_scale_per_relative_unit)*i+Number(e.inverse_offset_per_m);if(!Number.isFinite(t)||t<=0)return null;let n=1/t;return Math.max(.2,Math.min(15,n))}function hx(i,e=Ht){if(!e?.available)return null;let t=Number(e.inverse_scale_per_relative_unit)*i+Number(e.inverse_offset_per_m);if(!Number.isFinite(t)||t<=0)return null;let n=1/t;if(!Number.isFinite(n)||n<.2||n>15)return null;let r=e.calibrated_relative_range||[],s=Math.min(Number(r[0]),Number(r[1])),a=Math.max(Number(r[0]),Number(r[1]));return{meters:n,extrapolated:!Number.isFinite(s)||!Number.isFinite(a)||i<s||i>a}}function rh(i,e){let t=Math.floor(e/4);if(i.rawValues&&Number.isFinite(i.rawValues[t]))return i.rawValues[t];let n=i.values[e]/255;return Number.isFinite(i.rawMin)&&Number.isFinite(i.rawMax)?i.rawMin+n*(i.rawMax-i.rawMin):n}function Ac(i,e,t){let n=rh(i,e),r=Number.isFinite(i.rawMin)&&Number.isFinite(i.rawMax);if(t?.available&&r){let a=ux(n,t);if(Number.isFinite(a))return a}let s=sh(i,Math.floor(e/4));return 1/yt.lerp(1/5.5,1/.7,s)}function sh(i,e){let t=e%i.width,n=Math.floor(e/i.width),r=[];for(let s=-1;s<=1;s++)for(let a=-1;a<=1;a++){let o=yt.clamp(t+a,0,i.width-1),c=yt.clamp(n+s,0,i.height-1)*i.width+o,d=i.normalizedDepth?.[c]??(i.normalizedValues?.[c*4]??i.values[c*4])/255;Number.isFinite(d)&&r.push(d)}return r.sort((s,a)=>s-a),yt.clamp(r[Math.floor(r.length/2)]??0,0,1)}function ki(i){let e=kt?.intrinsics||kt?.camera_intrinsics||Zt?.intrinsics||Zt?.camera_intrinsics||{},t=Math.max(1,Number(i?.width)||640),n=Math.max(1,Number(i?.height)||480),r=Number(e.width||e.image_width||t),s=Number(e.height||e.image_height||n),a=t/r,o=n/s,l=Number(e.fx),c=Number(e.fy);if(l>0&&c>0&&Number.isFinite(Number(e.cx))&&Number.isFinite(Number(e.cy)))return{fx:l*a,fy:c*o,cx:Number(e.cx)*a,cy:Number(e.cy)*o,calibrated:!0};let d=t/(2*Math.tan(yt.degToRad(bs.horizontalFovDeg)/2));return{fx:d,fy:d,cx:(t-1)/2,cy:(n-1)/2,calibrated:!1}}function qt(i,e,t,n){return new N((i-n.cx)*t/n.fx,(n.cy-e)*t/n.fy,-t)}var $u={low_body_front:{heightM:.12},level_body_front:{heightM:.35},high_body_front:{heightM:.65}};function Ts(){let i=kt?.camera_profile||"low_body_front",e=$u[i]||$u.low_body_front,t=Number(kt?.camera_height_m??kt?.calibration?.height_m??Zt?.camera_height_m),n=Number.isFinite(t)&&t>0&&t<3?t:e.heightM,r=Number(kt?.camera_pitch_deg??kt?.calibration?.pitch_deg??Zt?.camera_pitch_deg),s=Number.isFinite(r)?r:0,a=new Wt().setFromAxisAngle(new N(1,0,0),yt.degToRad(s));return{profile:i,heightM:n,rotation:a,position:new N(0,n,0)}}function Vo(i=mt){if(!ue)return;let e=Ts(),t=Rc(i);Oi.quaternion.copy(t||new Wt);let n=Number(kt?.camera_height_m??kt?.calibration?.height_m??Zt?.camera_height_m),r=Number.isFinite(n)&&n>0,s=`${e.profile}:${e.heightM}:${r}`;s!==Gu&&(Gu=s,Oi.position.set(0,e.heightM,0),Lo&&(Lo.scale.y=e.heightM/.18),Fo&&Fo.position.copy(e.position),ko("origin",[{position:e.position.clone(),text:`BODY SENSOR ORIGIN \xB7 ${e.heightM.toFixed(2)} m above floor${r?"":" nominal"}`}]),ko("camera-mount",[{position:e.position.clone(),text:`CAMERA MOUNT \xB7 ${e.profile.replace(/_/g," ")} \xB7 ${e.heightM.toFixed(2)} m${r?"":" nominal"}`}]))}Vo();function ah(i,e=mt){let t=new N(0,Ts().heightM,0),n=Rc(e),r=i.clone();return n&&r.applyQuaternion(n),r.add(t)}function Yt(i,e=mt){let t=Ts();return ah(i.clone().applyQuaternion(t.rotation),e)}function oh(){if(!ue||!at)return;let i=ki(at),e=at.width,t=at.height,n=ue.camera.near,r=ue.camera.far;ue.camera.projectionMatrix.makePerspective(-i.cx*n/i.fx,(e-i.cx)*n/i.fx,i.cy*n/i.fy,-(t-i.cy)*n/i.fy,n,r),ue.camera.projectionMatrixInverse.copy(ue.camera.projectionMatrix).invert()}async function lh(i){if(!i?.frame_id)return null;try{let e=await fetch(`/body/camera/yolo-frame?frame_id=${encodeURIComponent(i.frame_id)}`,{cache:"no-store"});if(!e.ok)return null;let t=await e.json(),n=t.camera||{};return t.available&&n.frame_id===i.frame_id&&n.image_base64?n:null}catch(e){return console.warn("Could not load camera pixels paired with MiDaS frame:",e),null}}async function fx(i){if(pi?.frame_id===i?.frame_id)return pi;if(!Number.isFinite(Number(i?.captured_at)))return null;try{let e=new URLSearchParams({nearest_to:String(i.captured_at),max_delta_s:String(No)}),t=await fetch(`/body/camera/yolo/status?${e}`,{cache:"no-store"});if(!t.ok)return null;let n=await t.json(),r=Math.abs(Number(n.captured_at)-Number(i.captured_at));return n.state==="ready"&&Number.isFinite(r)&&r<=No?{...n,frame_delta_s:r}:null}catch(e){return console.warn("Could not find YOLOX detections near MiDaS frame:",e),null}}async function ch(i){if(!ue||!i?.image_base64)return!1;let e=++Ec,t=new Image;if(t.src=`data:${i.mime_type||"image/jpeg"};base64,${i.image_base64}`,await t.decode(),e!==Ec)return!1;let n=ki({width:t.naturalWidth,height:t.naturalHeight}),r=80,s=[Yt(qt(0,0,r,n),Number(i.captured_at)||mt),Yt(qt(t.naturalWidth,0,r,n),Number(i.captured_at)||mt),Yt(qt(0,t.naturalHeight,r,n),Number(i.captured_at)||mt),Yt(qt(t.naturalWidth,t.naturalHeight,r,n),Number(i.captured_at)||mt)],a=new Lt(t);a.colorSpace=Nt,a.needsUpdate=!0,$t&&(ue.scene.remove($t),$t.geometry.dispose(),$t.material.map?.dispose(),$t.material.dispose());let o=new dt;return o.setAttribute("position",new je(s.flatMap(l=>l.toArray()),3)),o.setAttribute("uv",new je([0,1,1,1,0,0,1,0],2)),o.setIndex([0,2,1,2,3,1]),$t=new st(o,new Xt({map:a,side:dn,depthWrite:!1})),$t.userData.frameId=i.frame_id,$t.renderOrder=-1,$t.visible=!!gt?.classList.contains("is-camera-view"),ue.scene.add($t),ue.render(),!0}async function dh(i){if(i?.depth_raw_png_base64&&Number.isFinite(Number(i.depth_raw_min))&&Number.isFinite(Number(i.depth_raw_max)))try{let n=await px(i.depth_raw_png_base64);return n.rawMin=Number(i.depth_raw_min),n.rawMax=Number(i.depth_raw_max),n.frameId=String(i.frame_id||""),n.capturedAt=Number(i.captured_at)||0,n.workerReceivedAt=Number(i.worker_received_at)||0,n.publishedAt=Number(i.published_at)||0,n.browserFetchedAt=Number(i.browser_fetched_at)||0,n}catch(n){console.warn("Could not decode raw 16-bit MiDaS depth; using preview:",n)}let t=await Mx(i.depth_gray_jpeg_base64,"image/jpeg");return t.normalizedValues=t.values,t.frameId=String(i.frame_id||""),t.capturedAt=Number(i.captured_at)||0,t.workerReceivedAt=Number(i.worker_received_at)||0,t.publishedAt=Number(i.published_at)||0,t.browserFetchedAt=Number(i.browser_fetched_at)||0,t}async function px(i){if(typeof DecompressionStream>"u")throw new Error("PNG decompression is unavailable");let e=Uint8Array.from(atob(i),T=>T.charCodeAt(0));if(![137,80,78,71,13,10,26,10].every((T,D)=>e[D]===T))throw new Error("Invalid PNG signature");let n=new DataView(e.buffer,e.byteOffset,e.byteLength),r=0,s=0,a=0,o=-1,l=0,c=[];for(let T=8;T+12<=e.length;){let D=n.getUint32(T),F=String.fromCharCode(...e.subarray(T+4,T+8)),B=T+8,k=B+D;if(k+4>e.length)throw new Error("Truncated PNG chunk");if(F==="IHDR"?(r=n.getUint32(B),s=n.getUint32(B+4),a=e[B+8],o=e[B+9],l=e[B+12]):F==="IDAT"&&c.push(e.subarray(B,k)),T=k+4,F==="IEND")break}if(!r||!s||a!==16||o!==0||l!==0)throw new Error("Expected non-interlaced 16-bit grayscale PNG");let d=c.reduce((T,D)=>T+D.length,0),u=new Uint8Array(d),h=0;for(let T of c)u.set(T,h),h+=T.length;let p=new Blob([u]).stream().pipeThrough(new DecompressionStream("deflate")),g=new Uint8Array(await new Response(p).arrayBuffer()),x=r*2;if(g.length!==(x+1)*s)throw new Error("Unexpected PNG scanline size");let m=new Uint8Array(x*s),f=(T,D,F)=>{let B=T+D-F,k=Math.abs(B-T),W=Math.abs(B-D),X=Math.abs(B-F);return k<=W&&k<=X?T:W<=X?D:F};for(let T=0;T<s;T++){let D=g[T*(x+1)],F=T*(x+1)+1,B=T*x;for(let k=0;k<x;k++){let W=g[F+k],X=k>=2?m[B+k-2]:0,H=T>0?m[B+k-x]:0,Q=T>0&&k>=2?m[B+k-x-2]:0,ne=D===0?0:D===1?X:D===2?H:D===3?Math.floor((X+H)/2):D===4?f(X,H,Q):NaN;if(!Number.isFinite(ne))throw new Error(`Unsupported PNG filter ${D}`);m[B+k]=W+ne&255}}let S=new Float32Array(r*s),M=new Uint32Array(65536),y=Number.NaN,C=Number.NaN;for(let T=0;T<S.length;T++){let D=m[T*2]<<8|m[T*2+1];S[T]=D,M[D]++}let E=T=>{let D=Math.floor((S.length-1)*T),F=0;for(let B=0;B<M.length;B++)if(F+=M[B],F>D)return B;return 65535},R=E(.02),P=Math.max(R+1,E(.98)),w=new Float32Array(S.length),v=new Uint8ClampedArray(S.length*4);for(let T=0;T<S.length;T++){let D=yt.clamp((S[T]-R)/(P-R),0,1);w[T]=D;let F=Math.round(D*255),B=T*4;v[B]=v[B+1]=v[B+2]=F,v[B+3]=255}return{width:r,height:s,values:v,rawValues:S,normalizedDepth:w,rawMin:y,rawMax:C}}function mx(i){return new tn({transparent:!0,depthWrite:!1,uniforms:{uPointSize:{value:i},uViewportHeight:{value:ue?.renderer.domElement.height||1},uOpacity:{value:.92}},vertexShader:`
      attribute float depthValue;
      uniform float uPointSize;
      uniform float uViewportHeight;
      varying float vDepth;
      void main() {
        vDepth = depthValue;
        vec4 viewPosition = modelViewMatrix * vec4(position, 1.0);
        gl_Position = projectionMatrix * viewPosition;
        gl_PointSize = max(1.0, uPointSize * uViewportHeight * 0.5 * projectionMatrix[1][1] / max(0.1, -viewPosition.z));
      }
    `,fragmentShader:`
      uniform float uOpacity;
      varying float vDepth;
      vec3 turbo(float x) {
        float x2 = x * x;
        float x3 = x2 * x;
        float x4 = x3 * x;
        float x5 = x4 * x;
        return clamp(vec3(
          0.13572138 + 4.61539260*x - 42.66032258*x2 + 132.13108234*x3 - 152.94239396*x4 + 59.28637943*x5,
          0.09140261 + 2.19418839*x + 4.84296658*x2 - 14.18503333*x3 - 4.27729857*x4 + 2.82956604*x5,
          0.10667330 + 12.64194608*x - 60.58204836*x2 + 110.36276771*x3 - 89.90310912*x4 + 27.34824973*x5
        ), 0.0, 1.0);
      }
      void main() {
        vec2 point = gl_PointCoord - vec2(0.5);
        float edge = 1.0 - smoothstep(0.42, 0.5, length(point));
        if (edge <= 0.01) discard;
        vec3 color = turbo(clamp(vDepth, 0.0, 1.0));
        gl_FragColor = vec4(color, uOpacity * edge);
      }
    `})}function Oo(){let i=["world-map-midas-calibration-status","world-map-midas-calibration-status-3d"].map(j).filter(Boolean);if(!i.length||ws)return;let e;if(Er)e=Er;else if(Ht?.available){let[t,n]=Ht.calibrated_range_m||[];e=`MiDaS fit \xB7 holdout \xB1${Number(Ht.holdout_rmse_m).toFixed(2)} m \xB7 ${Ht.sample_count} anchors \xB7 ${t}\u2013${n} m forward. Radar labels remain primary; camera alignment is approximate.`}else e="Not calibrated \xB7 ranges are relative, not metres. Track one person moving through several distances.";i.forEach(t=>{t.textContent=e})}async function gx(){try{let i=await fetch("/body/camera/depth-calibration",{cache:"no-store"});i.ok&&(Ht=await i.json())}catch(i){console.warn("Could not read persistent MiDaS calibration:",i)}Oo()}function Bo(i,e){return String(i.id||i.target_id||`target-${e}`)}function zo(i,e,t=null,n=null){if(!String(e?.source||"").toLowerCase().startsWith("hlk_ld2450"))return[];let s=Array.isArray(e.targets)?e.targets:[],a=(i||[]).filter(h=>/person|human/i.test(String(h.label||h.class_name||h.class||""))&&Number(h.confidence??h.score??0)>=.5&&Array.isArray(h.bbox)&&h.bbox.length===4),o=[];for(let[h,p]of s.entries()){let g=Bo(p,h);if(n!=null&&g!==String(n))continue;let x=p.position_m||p.position;if(!Array.isArray(x)||x.length<2)continue;let m=Number(x[0]),f=Number(x[1]),S=Math.hypot(m,f);if(!Number.isFinite(S)||S<.25||S>6||f<=0||Math.abs(Math.atan2(m,f))>Math.PI/3)continue;let M=m-bs.lateralOffsetM,y=Math.atan2(M,f)-yt.degToRad(bs.yawOffsetDeg);for(let C of a){let E=(Number(C.bbox[0])+Number(C.bbox[2]))/2,R=Number(t?.width)||Number(kt?.width)||640,P=ki({width:R,height:Number(t?.height)||480}),w=Math.atan2(E*R-P.cx,P.fx),v=yt.degToRad(bs.horizontalFovDeg);if(Math.abs(w)>v/2)continue;let T=Math.abs((w-y)*180/Math.PI);T>K0||o.push({detection:C,targetIndex:h,targetId:g,forward:f,radialRange:S,error:T,cost:T,lateralRight:M})}}o.sort((h,p)=>h.cost-p.cost);let l=o.filter(h=>{let p=o.filter(m=>m.detection===h.detection).sort((m,f)=>m.cost-f.cost),g=o.filter(m=>m.targetIndex===h.targetIndex).sort((m,f)=>m.cost-f.cost),x=m=>m[0]===h&&(!m[1]||m[1].cost-h.cost>=3);return x(p)&&x(g)}).sort((h,p)=>h.cost-p.cost),c=new Set,d=new Set;return l.filter(h=>c.has(h.detection)||d.has(h.targetIndex)?!1:(c.add(h.detection),d.add(h.targetIndex),!0))}function uh(){if(ws)return;let i=j("world-map-calibration-guide");i||(i=document.createElement("dialog"),i.id="world-map-calibration-guide",i.className="world-map-calibration-guide",i.setAttribute("aria-labelledby","world-map-calibration-title"),i.innerHTML=`<form method="dialog" class="world-map-calibration-guide__surface">
      <header><div><p class="world-map-calibration-kicker">BODY \xB7 SENSOR CALIBRATION</p><h2 id="world-map-calibration-title">Radar + MiDaS calibration</h2></div><button class="world-map-calibration-close" value="cancel" aria-label="Close guide">\xD7</button></header>
      <p class="world-map-calibration-intro">Follow the stages in order. This action collects radar-matched MiDaS anchors; it does not calibrate camera intrinsics or physically measure sensor alignment for you.</p>
      <label class="world-map-calibration-target" for="world-map-calibration-radar-target">Radar target to calibrate<select id="world-map-calibration-radar-target" required><option value="">Waiting for live radar targets\u2026</option></select><small>Choose the radar track belonging to the person visible to YOLOX. The collector will ignore all other radar targets.</small></label>
      <ol class="world-map-calibration-stages">
        <li><b>0 \xB7 Prepare the rig</b><span>Rigidly fix camera, radar and IMU on a level floor. Measure camera height and camera-to-radar lateral offset. Mark 1\u20135 m on the camera axis and \xB11 m at 2 m and 4 m.</span></li>
        <li><b>1 \xB7 IMU zero, about 5 s</b><span>Keep the robot still. The live IMU must report valid attitude, ready gyro bias, stable calibration and roll/pitch within \xB15\xB0. For a real mount zero, record level-floor roll/pitch offsets; the current fit only gates on low tilt.</span></li>
        <li><b>2 \xB7 Camera intrinsics \xB7 manual prerequisite</b><span>Calibrate at the live 640\xD7480 resolution with 15\u201320 checkerboard views. Save fx, fy, cx, cy and distortion to calibration/camera.json; target RMS below 0.5 px (at most 1 px).</span></li>
        <li><b>3 \xB7 Camera \u2194 radar alignment \xB7 manual prerequisite</b><span>At each tape mark, match a person\u2019s camera bearing with radar atan2(x,y). Verify the mount yaw/lateral offset and keep error under 3\xB0. Current automatic matching uses an approximate field of view; it does not fit these offsets.</span></li>
        <li><b>4 \xB7 Ground-plane check \xB7 optional</b><span>With measured camera height and IMU mount pitch, compare visible foot-point ranges to the tape marks. Target error under 0.2 m at 1\u20134 m. Not currently calculated by this button.</span></li>
        <li><b>5 \xB7 Fit MiDaS to radar \xB7 automated here</b><span>Stand still at several 1\u20135 m marks. The collector uses torso-region median depth, radar forward distance y, synchronized frames, a stable low-tilt IMU and unambiguous person matches. It needs at least 15 accepted anchors across four distance bands; the fit is robust and validates holdout data.</span></li>
        <li><b>6 \xB7 Validate \xB7 manual</b><span>Use tape marks omitted from fitting. Compare radar and MiDaS; test seated/cropped people too. Record the held-out RMSE. Treat predictions outside the fitted range as extrapolated.</span></li>
        <li><b>7 \xB7 Runtime</b><span>Radar remains the metric reference when a person is matched; MiDaS serves other objects. The rolling fit expires old anchors, so scene changes need fresh anchors. Recheck alignment after any impact/remount; redo intrinsics if lens or resolution changes.</span></li>
      </ol>
      <div class="world-map-calibration-checks"><label><input type="checkbox" data-calibration-check="rig"> Mounts are rigid; floor is level; tape marks are ready</label><label><input type="checkbox" data-calibration-check="imu"> Robot is stationary; IMU status is stable and low tilt</label><label><input type="checkbox" data-calibration-check="intrinsics"> I have verified the 640\xD7480 camera intrinsics</label><label><input type="checkbox" data-calibration-check="alignment"> I have measured/verified camera-to-radar alignment</label></div>
      <p class="world-map-calibration-caution">Intrinsics and alignment are not currently enforced by the fitter: without those checks, bearing matches and resulting distances remain approximate. Do not interpret a good MiDaS fit as proof of geometric calibration.</p>
      <p id="world-map-calibration-guide-status" class="world-map-calibration-progress" role="status">Ready when the robot and target person are stationary.</p>
      <footer><button type="button" data-calibration-action="cancel">Cancel</button><button type="button" data-calibration-action="start" class="primary">Start 60-second collection</button></footer>
    </form>`,document.body.appendChild(i),Cc(Sn),i.querySelector('[data-calibration-action="cancel"]')?.addEventListener("click",()=>i.close()),i.querySelector('[data-calibration-action="start"]')?.addEventListener("click",()=>{let e=[...i.querySelectorAll("[data-calibration-check]")].filter(r=>!r.checked),t=j("world-map-calibration-guide-status"),n=j("world-map-calibration-radar-target")?.value;if(!n){t.textContent="Select the radar target that matches the visible person before starting calibration.",j("world-map-calibration-radar-target")?.focus();return}if(e.length){t.textContent=`Verify the ${e.length} unchecked prerequisite${e.length===1?"":"s"}, or cancel and complete those calibration stages first.`,e[0].focus();return}i.close(),xx(n)}),i.addEventListener("click",e=>{e.target===i&&i.close()})),Cc(Sn),i.showModal()}function Cc(i){let e=j("world-map-calibration-radar-target");if(!e)return;let t=e.value||e.dataset.selectedTargetId||"",n=Array.isArray(i?.targets)?i.targets:[],r=[new Option(n.length?"Select the person\u2019s radar target\u2026":"Waiting for live radar targets\u2026","")];n.forEach((s,a)=>{let o=Bo(s,a),l=s.position_m||s.position||[],c=Number(l[0]),d=Number(l[1]),u=`${s.id||s.target_id||`Target ${a+1}`} \xB7 ${Number.isFinite(d)?`${d.toFixed(2)} m forward`:"range \u2014"} \xB7 ${Number.isFinite(c)?`${c.toFixed(2)} m lateral`:"bearing \u2014"}`;r.push(new Option(u,o))}),t&&!n.some((s,a)=>Bo(s,a)===t)&&r.push(new Option(`Selected target ${t} \xB7 waiting for radar return`,t)),e.replaceChildren(...r),t&&(e.value=t),e.dataset.selectedTargetId=e.value,e.onchange=()=>{e.dataset.selectedTargetId=e.value}}async function xx(i){if(ws)return;let e=["world-map-midas-calibrate","world-map-midas-calibrate-3d"].map(j).filter(Boolean),t=["world-map-midas-calibration-status","world-map-midas-calibration-status-3d"].map(j).filter(Boolean);if(!e.length||!t.length)return;let n=p=>t.forEach(g=>{g.textContent=p});ws=!0,Er="",e.forEach(p=>{p.disabled=!0,p.textContent="Calibrating\u2026"}),n(`Collecting target ${i} for 60 s: pause at several points from 1\u20135 m. Only synchronized, stationary, low-tilt matches to this radar target count.`);let r=[],s=new Set,a=new Set,o=new Set,l={depth:0,yolo:0,radar:0,framePairs:0,radarPairs:0,bearing:0,stationary:0,range:0},c="",d=null,u="",h=performance.now()+6e4;try{for(;performance.now()<h;){let p=await fetch("/body/camera/depth?include_raw=0&include_preview=0&include_color=0",{cache:"no-store"});if(!p.ok)throw new Error("MiDaS endpoint is unavailable");let g=await p.json();if(!g.frame_id||g.state!=="ready"){n(`Waiting for live MiDaS depth \xB7 ${r.length} anchors collected.`),await new Promise(X=>setTimeout(X,100));continue}g.frame_id!==u&&(l.depth+=1,u=g.frame_id);let x=Number(g.captured_at),m=Date.now()/1e3;if(!Number.isFinite(x)||m-x>6){await new Promise(X=>setTimeout(X,100));continue}let f=await fetch(`/body/camera/yolo/status?frame_id=${encodeURIComponent(g.frame_id)}`,{cache:"no-store"});if(f.ok||(f=await fetch(`/body/camera/yolo/status?nearest_to=${encodeURIComponent(g.captured_at)}&max_delta_s=${Sr}`,{cache:"no-store"})),!f.ok&&f.status!==404)throw new Error("YOLOX endpoint is unavailable");let S=f.ok?await f.json():null;if(!S||S.state!=="ready"){await new Promise(X=>setTimeout(X,100));continue}let M=Number(S.captured_at),y=Math.abs(M-x),C=(M+x)/2;a.has(S.frame_id)||(l.yolo+=1,a.add(S.frame_id));let E=`${g.frame_id}|${S.frame_id}`,R=String(S.frame_id||"")===String(g.frame_id);!o.has(E)&&(R||y<=Sr)&&m-M<=6&&(l.framePairs+=1,o.add(E));let P=Tr.filter(X=>(X.targets||[]).some((H,Q)=>Bo(H,Q)===i)).reduce((X,H)=>{let Q=Math.abs(Number(H.timestamp)-C);return!X||Q<X.delta?{item:H,delta:Q}:X},null),w=P?.delta??1/0;P&&w<=.75&&!o.has(`${E}|radar`)&&(l.radar+=1,o.add(`${E}|radar`));let v=(R||y<=Sr)&&m-M<=6&&m-x<=6,T=v&&P&&w<=Sr;T&&!o.has(`${E}|radar-pair`)&&(l.radarPairs+=1,o.add(`${E}|radar-pair`));let D=v&&P&&w<=.75?zo(S.detections,P.item,null,i):[];D.length&&!o.has(`${E}|bearing`)&&(l.bearing+=1,o.add(`${E}|bearing`)),D.some(X=>X.forward>=1&&X.forward<=5)&&!o.has(`${E}|range`)&&(l.range+=1,o.add(`${E}|range`));let F=Fi.filter(X=>X.calibration_stable&&X.attitude_valid).reduce((X,H)=>{let Q=Math.abs(Number(H.timestamp)-C);return Q<=Sr&&(!X||Q<X.age)?{sample:H,age:Q}:X},null)?.sample||null,B=F?Math.abs(Number(F.timestamp)-C):1/0,k=!!(F&&B<=Sr&&Math.abs(Number(F.roll_deg))<=5&&Math.abs(Number(F.pitch_deg))<=5);if(k&&!o.has(`${E}|imu`)&&(l.stationary+=1,o.add(`${E}|imu`)),T&&k&&D.length>0){if(c!==g.frame_id){let ne=await fetch("/body/camera/depth?include_raw=1&include_preview=0&include_color=0",{cache:"no-store"});if(!ne.ok)throw new Error("Raw MiDaS depth endpoint is unavailable");let fe=await ne.json();if(String(fe.frame_id||"")!==String(g.frame_id)||!fe.depth_raw_png_base64){await new Promise(De=>setTimeout(De,100));continue}d=await dh(fe),c=g.frame_id}let H=zo(S.detections,P.item,d,i).filter(ne=>ne.forward>=1&&ne.forward<=5).find(ne=>ne.targetId===i)||null,Q=`${g.frame_id}|${S.frame_id}`;if(H&&d&&!s.has(Q)){let ne=H.detection.bbox.map(Number),fe=Math.max(0,Math.min(d.width-1,Math.round((ne[0]*.7+ne[2]*.3)*d.width))),De=Math.max(fe+1,Math.min(d.width,Math.round((ne[0]*.3+ne[2]*.7)*d.width))),Xe=Math.max(0,Math.min(d.height-1,Math.round((ne[1]*.65+ne[3]*.35)*d.height))),Ze=Math.max(Xe+1,Math.min(d.height,Math.round((ne[1]*.35+ne[3]*.65)*d.height))),Fe=[],Y=Math.max(1,Math.floor(Math.min(De-fe,Ze-Xe)/8));for(let ze=Xe;ze<Ze;ze+=Y)for(let xt=fe;xt<De;xt+=Y)Fe.push(rh(d,(ze*d.width+xt)*4));if(Fe.sort((ze,xt)=>ze-xt),!Fe.length)continue;let J=Fe[Math.floor(Fe.length/2)],pe={sample_id:`${g.frame_id}|${S.frame_id}|${H.targetId}`,relative_depth:J,forward_m:H.forward,bearing_error_deg:H.error,frame_delta_s:y,frame_id_match:R,radar_delta_s:w,imu_delta_s:B,stationary:!0},Ce=await fetch("/body/camera/depth-calibration",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({sample:pe})});if(!Ce.ok)throw new Error("Rolling calibration endpoint rejected an anchor");let ge=await Ce.json();if(!ge.accepted){s.add(Q);continue}r.push(pe),s.add(Q),Ht=ge.available?ge:null,Er=ge.available?"":ge.reason||"Collecting a wider set of stationary anchors.",Oo()}}n(`Anchors ${r.length}/15 \xB7 depth ${l.depth} \xB7 YOLO/depth sync ${l.framePairs} \xB7 radar/depth sync ${l.radarPairs} \xB7 bearing ${l.bearing} \xB7 stationary IMU ${l.stationary} \xB7 1\u20135 m targets ${l.range}.`),await new Promise(X=>setTimeout(X,100))}if(!Ht?.available){let p=l.framePairs===0?"No YOLOX/depth pairs met the 250 ms sync limit; check worker cadence and frame timestamps.":l.radarPairs===0?"No radar/depth pairs met the 250 ms sync limit; verify radar timestamps and keep the target still.":l.bearing===0?"No camera-person/radar bearing match; verify target identity, camera FOV, mount yaw and lateral offset.":l.stationary===0?"IMU did not confirm stable stationary posture; keep the body still and wait for gyro bias.":"Collect a person at four or more distance bands from 1\u20135 m; nearer/ farther radar targets are excluded.";throw new Error(`Fit not validated; collected ${r.length} anchors. ${p}`)}Ar="",Er="",wc=0,await Pc()}catch(p){Er=`Calibration not saved: ${p.message} \xB7 depth ${l.depth}, YOLO ${l.yolo}, radar \u22640.75 s ${l.radar}, frame pairs \u2264250 ms ${l.framePairs}, radar pairs \u2264250 ms ${l.radarPairs}, bearing matches ${l.bearing}, stable IMU ${l.stationary}, in-range ${l.range}`}finally{ws=!1,e.forEach(p=>{p.disabled=!1,p.textContent=Ht?.available?"Recalibrate with radar":"Calibrate with radar"}),Oo()}}async function Ic(){if(!(gc||ut!=="sensors")){gc=!0;try{let e=await(await fetch("/body/camera/frame",{cache:"no-store"})).json();Do("camera",!1);let t=e.camera||{},n=e.yolo||{};kt=t,Vo(),pi=n;let r=j("world-map-camera-state"),s=Number(t.captured_at)>0?Math.max(0,Date.now()/1e3-Number(t.captured_at)):1/0;r&&(r.textContent=t.image_base64?`LIVE \xB7 ${t.width||"\u2014"}\xD7${t.height||"\u2014"} \xB7 ${Number.isFinite(s)?s.toFixed(1)+"s":"age \u2014"}`:`${t.state||e.status||"NO FRAME"}`),Tt("world-map-camera-state","camera",Jn("camera",s,!!t.image_base64),t.image_base64?`LIVE \xB7 ${t.width||"\u2014"}\xD7${t.height||"\u2014"} \xB7 ${Number.isFinite(s)?s.toFixed(1)+"s":"age \u2014"}`:`${t.state||e.status||"NO FRAME"}`);let a=j("world-map-camera-image"),o=j("world-map-camera-empty");t.frame_id!==Fu&&(ih(a,o,t.image_base64,t.mime_type||"image/jpeg"),Fu=t.frame_id);let l=a?.parentElement;l&&t.width&&t.height&&(l.style.aspectRatio=`${t.width}/${t.height}`);let c=lx(n),d=Number(n.captured_at)>0?Date.now()/1e3-Number(n.captured_at):1/0,u=`${n.state||"disabled"}:${n.frame_id||""}:${c.map(m=>`${m.overlayAgeS.toFixed(1)}:${m.bbox.join(",")}`).join(";")}`;u!==Uu&&(sx(c,t.width||640,t.height||480),Uu=u),Rt==="3d"&&at&&Wo(at,Ss),Rt==="3d"&&Zn();let h=`${n.state||"disabled"} \xB7 ${(n.detections||[]).length} boxes${n.latency_ms!=null?` \xB7 ${n.latency_ms} ms`:""}${n.paired===!1?" \xB7 waiting for paired frame":""}`,p=n.paired===!1&&n.state==="stale"?"stale":Jn("yolo",d,n.state==="ready"&&!!t.image_base64&&n.paired!==!1);Tt("world-map-yolo-state","yolo",p,h);let g=t.frame_id?`${t.frame_id}${t.captured_at?` \xB7 ${s.toFixed(1)}s`:""}`:"No frame";j("world-map-frame-state").textContent=g;let x=j("world-map-summary-frame");x&&(x.textContent=Number.isFinite(s)?`${s.toFixed(1)} s`:"\u2014"),j("world-map-sensor-note").textContent=`Sensor-only view \xB7 frame ${t.frame_id||"unavailable"} \xB7 no simulation object positions or metric scale.`}catch(i){Tt("world-map-camera-state","camera","offline",`Offline \xB7 ${i.message}`),Tt("world-map-yolo-state","yolo","offline","Offline \xB7 waiting for camera frame"),Do("camera",!0),j("world-map-sensor-note").textContent=kt?.frame_id?`Sensor-only view \xB7 last camera frame ${kt.frame_id} is retained but not current.`:"Sensor-only view \xB7 waiting for a current camera frame."}finally{gc=!1}}}async function As(i){let e=await fetch(i,{cache:"no-store"});if(!e.ok)throw new Error(`HTTP ${e.status}`);return e.json()}var pn={radar:!1,gps:!1,imu:!1,tof:!1},yc=!1,Mt=(i,e=1,t="")=>{let n=i==null||i===""?NaN:Number(i);return Number.isFinite(n)?`${n.toFixed(e)}${t}`:"\u2014"};async function _x(){if(!(yc||ut!=="sensors")){yc=!0;try{let i=await As("/system/metrics"),e=i.cpu||{},t=i.gpu||{},n=i.memory||{},r=i.power||{};j("world-map-system-state").textContent=i.available?"Live \xB7 1 s":"Partial telemetry";let s=(h,p,g,x,m="")=>{let f=j(h),S=p!=null&&p!==""&&Number.isFinite(Number(p)),M=S?Math.max(0,Math.min(Number(g),Number(p))):0;f.style.setProperty("--gauge-value",S?String(M/Number(g)*100):"0"),f.setAttribute("aria-label",`${x}: ${S?`${Number(p).toFixed(1)}${m}`:"unavailable"}`)};s("world-map-cpu-gauge",e.utilization_percent,100,"CPU utilization","%"),s("world-map-cpu-temp-gauge",e.temperature_c,100,"Maximum CPU temperature"," degrees Celsius"),s("world-map-gpu-temp-gauge",t.temperature_c,100,"Maximum GPU temperature"," degrees Celsius"),s("world-map-memory-gauge",n.used_percent,100,"Memory utilization","%"),j("world-map-system-cpu-value").textContent=e.utilization_percent==null?"\u2014":e.utilization_percent.toFixed(0),j("world-map-system-cpu-temp-value").textContent=Mt(e.temperature_c,1),j("world-map-system-gpu-temp-value").textContent=Mt(t.temperature_c,1),j("world-map-system-cpu-temp").textContent=`Hottest CPU \xB7 ${Mt(e.temperature_c,1,"\xB0C")}`;let a=t.frequency_mhz==null?"\u2014":`${t.frequency_mhz.toFixed(0)} MHz`;j("world-map-system-gpu-meta").textContent=`${t.utilization_percent==null?"Load unavailable":`${t.utilization_percent.toFixed(1)}% load`} \xB7 ${a}`,j("world-map-system-gpu-load").textContent=t.utilization_percent==null?"Not exposed by kernel":`${t.utilization_percent.toFixed(1)}%`,j("world-map-system-gpu-clock").textContent=a,j("world-map-system-memory-value").textContent=n.used_percent==null?"\u2014":n.used_percent.toFixed(0),j("world-map-system-memory-meta").textContent=n.available_mb==null?"Free memory unavailable":`${(n.available_mb/1024).toFixed(1)} / ${(n.total_mb/1024).toFixed(1)} GB free`;let o=Math.max(20,Math.ceil((Number(r.watts)||0)/10)*10);s("world-map-power-gauge",r.watts,o,"Measured board input power"," watts"),j("world-map-power-gauge").setAttribute("aria-label",r.available?`Measured board input power: ${r.watts.toFixed(2)} watts on a 0 to ${o} watt display scale`:"Measured board input power unavailable"),j("world-map-system-power-value").textContent=r.available?r.watts.toFixed(1):"\u2014";let l=j("world-map-summary-power"),c=j("world-map-summary-energy");l&&(l.textContent=r.available?`${r.watts.toFixed(1)} W`:"\u2014 W"),c&&(c.textContent=r.available?`${r.energy_wh_session.toFixed(3)} Wh`:"\u2014 Wh"),j("world-map-system-power-meta").textContent=r.available?`${r.voltage_v.toFixed(1)} V \xB7 ${r.current_a.toFixed(2)} A \xB7 scale 0\u2013${o} W`:"Onboard power monitor unavailable";let d=String(pi?.runtime||"").toLowerCase().includes("htp"),u=String(Zt?.device||"").toLowerCase().includes("htp");j("world-map-system-htp").textContent=d||u?`ACTIVE \xB7 YOLOX ${d?`${Mt(pi?.inference_ms,0," ms")} HTP`:"\u2014"} \xB7 MiDaS ${u?`${Mt(Zt?.inference_ms,0," ms")} HTP`:"\u2014"}`:"Utilization counter unavailable",j("world-map-system-energy").textContent=r.available?`${r.energy_wh_session.toFixed(3)} Wh`:"Unavailable",j("world-map-system-note").textContent="The INA232 monitors the onboard input rail; external motor loads may be excluded. Temperature dials show the hottest reported sensor in each group; GPU/HTP utilization is unavailable because the kernel exports no reliable busy counter."}catch(i){j("world-map-system-state").textContent=`Unavailable \xB7 ${i.message}`}finally{yc=!1}}}function qu(i={}){let e=j("world-map-radar-plot"),t=e?.getContext("2d");if(!t)return;let n=Math.min(window.devicePixelRatio||1,2),r=Math.max(1,e.clientWidth),s=Math.max(1,e.clientHeight);(e.width!==Math.round(r*n)||e.height!==Math.round(s*n))&&(e.width=Math.round(r*n),e.height=Math.round(s*n)),t.setTransform(n,0,0,n,0,0),t.clearRect(0,0,r,s);let a=38,o=r-22,l=18,c=s-28,d=(a+o)/2;t.strokeStyle="#294c3a",t.fillStyle="#8eaa98",t.font="10px ui-monospace,monospace";for(let h=1;h<=6;h+=1){let p=c-(c-l)*h/6;t.globalAlpha=h%2?.55:.9,t.beginPath(),t.moveTo(a,p),t.lineTo(o,p),t.stroke(),t.fillText(`${h}m`,6,p+3)}t.globalAlpha=1;for(let h=-60;h<=60;h+=30){let p=d+Math.tan(h*Math.PI/180)/Math.tan(Math.PI/3)*(o-a)/2;t.beginPath(),t.moveTo(p,l),t.lineTo(p,c),t.stroke(),t.fillText(`${h>0?"+":""}${h}\xB0`,p-10,s-8)}t.fillStyle="#b6f1d3",t.beginPath(),t.moveTo(d,c-9),t.lineTo(d-6,c+1),t.lineTo(d+6,c+1),t.closePath(),t.fill();let u=Array.isArray(i.targets)?i.targets:[];for(let h of u){let p=h.position_m||h.position||[],g=Number(p[0]),x=Number(p[1]);if(!Number.isFinite(g)||!Number.isFinite(x)||x<0||x>6)continue;let m=Math.atan2(g,x);if(Math.abs(m)>Math.PI/3)continue;let f=d+m/(Math.PI/3)*(o-a)/2,S=c-x/6*(c-l),M=Number(h.radial_speed_mps),y=Number(hn?.captured_at)>0?Date.now()/1e3-Number(hn.captured_at):1/0,C=hn?.available&&y<=.35&&Number(hn.confidence)>=.35&&Number(hn.speed_mps)>=.05,E=Number.isFinite(M)&&Math.abs(M)>=.05&&!C;t.fillStyle=C?"#9aa7ad":E?"#ed91c5":"#efcb76",t.beginPath(),t.arc(f,S,5,0,Math.PI*2),t.fill(),t.fillStyle="#e7f4eb",t.font="10px ui-monospace,monospace",t.fillText(`${x.toFixed(1)}m`,f+8,S-5)}}async function hh(){if(!(ut!=="sensors"||pn.radar)){pn.radar=!0;try{let i=await As("/plugins/mmwave_radar/status"),e=i.sample||{};Sn=i.available?e:null,Sn?.timestamp&&!Tr.some(a=>a.timestamp===Sn.timestamp)&&(Tr.push(Sn),Tr=Tr.filter(a=>Date.now()/1e3-Number(a.timestamp)<=12).slice(-128));let t=Array.isArray(e.targets)?e.targets:[];Cc(Sn);let n=Number(e.timestamp)>0?Math.max(0,Date.now()/1e3-Number(e.timestamp)):NaN,s=`${`${t.length} target${t.length===1?"":"s"}`}${Number.isFinite(n)?` \xB7 ${n.toFixed(1)} s`:""}`;Tt("world-map-radar-state","radar",Jn("radar",n,!!i.available),i.available?s:i.error||"No data"),j("world-map-radar-targets").replaceChildren(...t.length?t.map((a,o)=>{let l=a.position_m||a.position||[],c=a.velocity_mps||a.velocity||[],d=Number(l[0]),u=Number(l[1]),h=document.createElement("div");h.className="sensor-target-row";let p=document.createElement("span");p.textContent=`${a.id||a.target_id||`Target ${o+1}`} \xB7 ${a.classification||"unclassified"}`;let g=document.createElement("b");return g.textContent=`${Number.isFinite(u)?u.toFixed(2):"\u2014"} m fwd \xB7 ${Number.isFinite(d)?d.toFixed(2):"\u2014"} m lat \xB7 ${Mt(a.radial_speed_mps,2," m/s")}`,h.append(p,g),h.title=`XY velocity ${Mt(c[0],2)} / ${Mt(c[1],2)} m/s \xB7 confidence ${Mt(a.confidence,2)}`,h}):[Object.assign(document.createElement("span"),{textContent:i.available?"No targets in current radar frame.":"Waiting for a live radar frame."})]),qu(e),zi(Sn)}catch(i){Sn=null,Tt("world-map-radar-state","radar","offline",`Unavailable \xB7 ${i.message}`),j("world-map-radar-state").textContent=`Unavailable \xB7 ${i.message}`,j("world-map-radar-targets").textContent="No live radar data.",qu(),zi(null)}finally{pn.radar=!1}}}async function fh(){if(!(ut!=="sensors"||pn.gps)){pn.gps=!0;try{let i=await As("/plugins/gps/status"),e=i.sample||i.source_status?.sample||{},t=i.source_status?.diagnostic||{},n=!!(i.available||e.connected||Number(t.bytes_received)>0),r=e.fix===!0||e.valid===!0||Number(e.fix_quality)>0,s=Number(e.timestamp)>0?Math.max(0,Date.now()/1e3-Number(e.timestamp)):NaN,a=Jn("gps",s,n);Tt("world-map-gps-state","gps",a,r?"Fix valid":n?"UART live \xB7 no fix":i.error||"Offline");let o=Number(e.latitude_deg??e.latitude??e.lat),l=Number(e.longitude_deg??e.longitude??e.lon??e.lng);j("world-map-gps-position").textContent=r&&Number.isFinite(o)&&Number.isFinite(l)?`${o.toFixed(6)}, ${l.toFixed(6)}`:"No valid fix",j("world-map-gps-fix").textContent=`${a==="stale"?"Stale fix":a==="live"&&r?"Valid":"No fix"} \xB7 quality ${e.fix_quality??"\u2014"}`,j("world-map-gps-satellites").textContent=`${e.satellites??"\u2014"} used \xB7 ${e.satellites_in_view??"\u2014"} in view`,j("world-map-gps-quality").textContent=`HDOP ${Mt(e.hdop)} \xB7 ${Mt(e.altitude_m,1," m")}`;let c=Array.isArray(e.satellite_signals)?e.satellite_signals:[],d=j("world-map-gps-signals");d.setAttribute("aria-label",`GPS satellite signal strength; ${c.length} satellites reported`);let u=c.slice(0,12),h=u.map(p=>{let g=Number(p.cn0_db_hz),x=Number.isFinite(g)?Math.max(3,Math.min(60,g)):3,m=document.createElement("div");m.className="sensor-gps-bar";let f=`${String(p.talker||"GN").replace(/[^a-z0-9]/gi,"")}-${Number(p.svid)||"?"}`,S=document.createElement("span");S.textContent=Number.isFinite(g)?g.toFixed(0):"\u2014";let M=document.createElement("i");M.style.height=`${x}px`,M.style.background=g>=35?"#3d9f70":g>=25?"#c39738":"#bd6559";let y=document.createElement("small");return y.textContent=f,m.title=`${f} \xB7 C/N\u2080 ${Mt(g,0," dB-Hz")} \xB7 az ${p.azimuth_deg??"\u2014"}\xB0 \xB7 el ${p.elevation_deg??"\u2014"}\xB0`,m.append(S,M,y),m});if(c.length>u.length){let p=document.createElement("span");p.className="sensor-gps-more",p.textContent=`+${c.length-u.length}`,p.title=`${c.length-u.length} additional satellites`,h.push(p)}d.replaceChildren(...c.length?h:[Object.assign(document.createElement("span"),{className:"sensor-readout-note",textContent:i.available?"No GSV satellite signal values in the current GPS sample.":"Waiting for GSV data from the GPS receiver."})])}catch(i){Tt("world-map-gps-state","gps","offline",`Unavailable \xB7 ${i.message}`)}finally{pn.gps=!1}}}async function ph(){if(!(ut!=="sensors"||pn.imu)){pn.imu=!0;try{let i=await As("/plugins/imu/status"),e=i.sample||{};Array.isArray(i.history)?Fi=i.history.slice(-256):e.sequence!=null&&!Fi.some(a=>a.sequence===e.sequence)&&(Fi.push(e),Fi=Fi.slice(-256));let t=Number(e.timestamp)>0?Math.max(0,Date.now()/1e3-Number(e.timestamp)):NaN;Tt("world-map-imu-state","imu",Jn("imu",t,!!i.available),i.available?`${e.attitude_valid?"Fused attitude":"Fused attitude unavailable"} \xB7 ${e.motion_state||"motion unknown"}${e.gyro_bias_ready?" \xB7 bias ready":" \xB7 bias warming"}`:i.error||"No data"),j("world-map-imu-roll").textContent=e.attitude_valid?Mt(e.roll_deg,1,"\xB0"):"Invalid",j("world-map-imu-pitch").textContent=e.attitude_valid?Mt(e.pitch_deg,1,"\xB0"):"Invalid";let n=j("world-map-imu-attitude");if(n){let a=Number(e.roll_deg),o=Number(e.pitch_deg),l=!!e.attitude_valid&&Number.isFinite(a)&&Number.isFinite(o);n.dataset.state=l?"live":"offline",l&&(n.style.setProperty("--imu-roll",`${a}deg`),n.style.setProperty("--imu-pitch",`${Math.max(-18,Math.min(18,o*.7))}px`))}j("world-map-imu-yaw").textContent=`${Mt(e.yaw_relative_deg,1,"\xB0")} rel \xB7 ${Mt(e.yaw_rate_dps??e.angular_velocity_dps?.[2],1,"\xB0/s")}`;let r=e.acceleration_g;j("world-map-imu-accel").textContent=Array.isArray(r)?r.map(a=>Mt(a,2)).join(" / "):"\u2014";let s=e.angular_velocity_dps;j("world-map-imu-gyro").textContent=Array.isArray(s)?s.map(a=>Mt(a,1)).join(" / "):"\u2014"}catch(i){Tt("world-map-imu-state","imu","offline",`Unavailable \xB7 ${i.message}`)}finally{pn.imu=!1}}}async function mh(){if(!(ut!=="sensors"||pn.tof)){pn.tof=!0;try{let i=await As("/plugins/tof/status"),e=i.sample||{},t=Number(e.timestamp)>0?Math.max(0,Date.now()/1e3-Number(e.timestamp)):NaN,n=i.available&&e.available!==!1&&!e.simulated&&!/sensor_not_detected/i.test(String(i.error||"")),r=Jn("tof",t,n);Tt("world-map-tof-state","tof",r,r==="stale"?`Stale \xB7 ${t.toFixed(1)} s`:n?`${e.device||i.sensor||"VL53L1X"} \xB7 live`:i.error||"No fresh measurement"),j("world-map-tof-distance").textContent=n?Mt(e.distance_m,2," m"):"No measurement",j("world-map-tof-meta").textContent=n?`${e.frame||i.frame||"body_front"} \xB7 ${Mt(e.distance_mm,0," mm")}`:i.transport||"Forward single-beam range"}catch(i){Tt("world-map-tof-state","tof","offline",`Unavailable \xB7 ${i.message}`)}finally{pn.tof=!1}}}async function yx(){if(!(xc||ut!=="sensors")){xc=!0;try{let e=await(await fetch("/body/camera/segmentation",{cache:"no-store"})).json();if(Cr=e,dx(e).catch(n=>{let r=j("world-map-segmentation-classes");r&&(r.textContent=`SegFormer mask unavailable \xB7 ${n.message}`)}),j("world-map-segmentation-state")){let n=Number(e.captured_at)>0?Math.max(0,Date.now()/1e3-Number(e.captured_at)):NaN,r=Number.isFinite(n)?` \xB7 ${n.toFixed(1)}s old`:"",s=!!(e.available||e.mask_png_base64||e.class_mask),a=Jn("segmentation",n,s&&e.state!=="disabled");Tt("world-map-segmentation-state","segmentation",a,`${e.state||"disabled"}${e.device?` \xB7 ${e.device}`:""}${e.latency_ms!=null?` \xB7 ${e.latency_ms} ms`:""}${r}`)}}catch(i){j("world-map-segmentation-state")&&Tt("world-map-segmentation-state","segmentation","offline",`SegFormer unavailable \xB7 ${i.message}`)}finally{xc=!1}}}async function Pc(){if(!(fc||ut!=="sensors"||Zt&&performance.now()-wc<100)){fc=!0;try{let i=Rt==="3d"?Ar:String(j("world-map-depth-image")?.dataset.frameId||""),e=new URLSearchParams({include_raw:Rt==="3d"&&Ht?.available?"1":"0",include_preview:"1",include_color:Rt==="3d"?"0":"1"});i&&e.set("since_frame_id",i);let n=await(await fetch(`/body/camera/depth?${e}`,{cache:"no-store"})).json();Do("depth",!1);let r=Cr;Zt=n,Cr=r,wc=performance.now();let s=Number(n.captured_at)>0?` \xB7 ${Math.max(0,Date.now()/1e3-Number(n.captured_at)).toFixed(1)}s old`:"",a=Number(n.captured_at)>0?Math.max(0,Date.now()/1e3-Number(n.captured_at)):NaN,o=Jn("midas",a,!!n.available&&n.state!=="disabled");if(Tt("world-map-midas-state","midas",o,`${n.state||"disabled"}${n.device?` \xB7 ${n.device}`:""}${n.latency_ms!=null?` \xB7 ${n.latency_ms} ms`:""}${s}${n.error?` \xB7 ${n.error}`:""}`),n.unchanged||!n.frame_id){Zn();return}n.browser_fetched_at=Date.now()/1e3,tt&&(tt.material.uniforms.uOpacity.value=.92),Oo();let l=yh(r,n)?String(r.frame_id||r.captured_at||""):"",c=`${n.frame_id||""}:${Number(n.captured_at)||0}:${l}`,d=`${Ar}:${mt}:${Mc}`,u=Rt==="3d"&&c!==d&&c!==Io,h=Rt!=="3d"&&n.frame_id&&j("world-map-depth-image")?.dataset.frameId!==String(n.frame_id);if((u||h)&&n.frame_id){let p=String(n.frame_id);if(n.depth_jpeg_base64&&(ih(j("world-map-depth-image"),j("world-map-depth-empty"),n.depth_jpeg_base64),j("world-map-depth-image").dataset.frameId=p),u&&n.depth_gray_jpeg_base64){Io=c;try{await Sx(n,r)&&(Ar=p,Mc=l)}finally{Io===c&&(Io="")}}}}catch(i){Tt("world-map-midas-state","midas","offline",`unavailable \xB7 ${i.message}`),tt&&(tt.visible=!1,ue.render()),Do("depth",!0)}finally{fc=!1}}}var vc=!1;async function vx(){if(!(vc||ut!=="sensors")){vc=!0;try{let e=await(await fetch("/body/odometry/visual",{cache:"no-store"})).json();if(!j("world-map-odometry-state"))return;let n=j("world-map-odometry-map-status");n&&(n.textContent=e.available?"TRACKING":`${String(e.state||"waiting").toUpperCase()} \xB7 LAST FIX RETAINED`,n.title=e.reason||"");let r=Number(e.captured_at)>0?Math.max(0,Date.now()/1e3-Number(e.captured_at)):NaN,s=Jn("odometry",r,!!e.available);if(e.available){let[a=0,o=0]=e.position_m||[];Tt("world-map-odometry-state","odometry",s,`${a.toFixed(2)}m fwd \xB7 ${o.toFixed(2)}m left \xB7 ${Math.round(e.confidence*100)}% \xB7 experimental`);let l=String(e.frame_id||"");l&&l!==Bu&&(Bu=l,Yn.push({forward:a,lateral:o}),Yn.length>600&&Yn.shift(),Es()),bx(e)}else Tt("world-map-odometry-state","odometry","offline",`${e.state||"waiting"} \xB7 ${e.reason||"need synchronized camera, MiDaS and radar calibration"}`),n&&(n.title=e.reason||"")}catch(i){j("world-map-odometry-state")&&Tt("world-map-odometry-state","odometry","offline",`unavailable \xB7 ${i.message}`)}finally{vc=!1}}}function bx(i){hn=i,gh();let e=j("world-map-odometry-map-status");e&&(e.textContent=`TRACKING \xB7 ${Number(i.speed_mps||0).toFixed(2)} m/s`)}function gh(){let i=j("world-map-odometry-map"),e=i?.parentElement;if(!i||!e)return;let t=e.getBoundingClientRect();if(!t.width||!t.height)return;let n=Math.max(1,window.devicePixelRatio||1),r=Math.round(t.width*n),s=Math.round(t.height*n);(i.width!==r||i.height!==s)&&(i.width=r,i.height=s);let a=i.getContext("2d");a.setTransform(n,0,0,n,0,0);let o=t.width,l=t.height;a.fillStyle="#050b12",a.fillRect(0,0,o,l),a.strokeStyle="#1b3042",a.lineWidth=1;for(let M=0;M<=o;M+=Math.max(48,o/8))a.beginPath(),a.moveTo(Math.round(M)+.5,0),a.lineTo(Math.round(M)+.5,l),a.stroke();for(let M=0;M<=l;M+=Math.max(40,l/6))a.beginPath(),a.moveTo(0,Math.round(M)+.5),a.lineTo(o,Math.round(M)+.5),a.stroke();let c=Math.min(28,o*.08),d={left:c,right:o-c,top:c,bottom:l-c},u={x:o/2,y:l*.68},h=Math.max(1,...Yn.map(M=>Math.abs(M.forward))),p=Math.max(1.4,...Yn.map(M=>Math.abs(M.lateral))),g=Math.min((d.right-d.left)/(2*p),(u.y-d.top)/h,(d.bottom-u.y)/h);a.strokeStyle="#00aeb8",a.beginPath(),a.moveTo(u.x,d.top),a.lineTo(u.x,d.bottom),a.stroke(),a.beginPath(),a.moveTo(d.left,d.bottom),a.lineTo(d.right,d.bottom),a.stroke(),Yn.length>1&&(a.strokeStyle="#ed35c5",a.lineWidth=2,a.beginPath(),Yn.forEach((M,y)=>{let C=u.x-M.lateral*g,E=u.y-M.forward*g;y?a.lineTo(C,E):a.moveTo(C,E)}),a.stroke());let x=hn,m=j("world-map-odometry-position"),[f=0,S=0]=x?.position_m||[];m&&(m.textContent=`${f.toFixed(2)} m fwd \xB7 ${S.toFixed(2)} m left`),a.save(),a.translate(u.x-S*g,u.y-f*g),a.rotate(Number(x?.yaw_rad)||0),a.fillStyle="#00d6df",a.strokeStyle="#e8ffff",a.lineWidth=1,a.beginPath(),a.moveTo(0,-10),a.lineTo(7,8),a.lineTo(0,5),a.lineTo(-7,8),a.closePath(),a.fill(),a.stroke(),a.restore()}function Go(){if(ue){if(ue.resize(),tt&&(tt.material.uniforms.uViewportHeight.value=ue.renderer.domElement.height),gt?.classList.contains("is-camera-view")&&oh(),tt&&(!Sc||!ue.camera.userData.userAdjusted)){tt.geometry.boundingBox||tt.geometry.computeBoundingBox();let i=tt.geometry.boundingBox,e=i.getCenter(new N),t=i.getSize(new N),n=yt.degToRad(ue.camera.fov),r=2*Math.atan(Math.tan(n/2)*ue.camera.aspect),s=t.y/(2*Math.tan(n/2)),a=t.x/(2*Math.tan(r/2)),o=Math.max(s,a,.8)*.82+t.z*.18;ue.camera.userData.target=e,ue.camera.position.copy(e).add(new N(0,Math.max(.2,t.y*.1),o)),Sc=!0}ue.camera.lookAt(ue.camera.userData.target||new N),ue.render()}}function wx(i){if(!ue||!tt)return;if(i==="camera"){gt?.classList.add("is-camera-view"),ue.resize();let a=ki(at);ue.camera.fov=yt.radToDeg(2*Math.atan((at?.height||480)/(2*a.fy))),ue.camera.userData.userAdjusted=!0;let o=Ts(),c=(Rc(mt)||new Wt).multiply(o.rotation),d=new N(0,0,-1).applyQuaternion(c);ue.camera.userData.target=o.position.clone().add(d),ue.camera.position.copy(o.position),ue.camera.up.set(0,1,0).applyQuaternion(c),ue.camera.lookAt(ue.camera.userData.target),oh(),zi(),Es(),Zn();let u=Zt;u&&lh(u).then(async h=>Zt?.frame_id!==u.frame_id?!1:h?ch(h):($t&&($t.visible=!1),Zn(),!1)).then(()=>ue.render()).catch(h=>console.warn("Could not load camera-aligned 3D background:",h)),ue.render();return}gt?.classList.remove("is-camera-view"),ue.camera.fov=42,ue.resize(),tt.geometry.boundingBox||tt.geometry.computeBoundingBox();let e=tt.geometry.boundingBox,t=e.getCenter(new N),n=e.getSize(new N),r=Math.max(n.x,n.y,n.z,2)*.95,s={top:new N(0,r,-.01),side:new N(r,Math.max(.2,n.y*.12),0),follow:new N(0,Math.max(.7,n.y*.24),r*.78)};ue.camera.userData.userAdjusted=!0,ue.camera.userData.target=t,ue.camera.position.copy(t).add(s[i]||s.follow),ue.camera.up.set(0,i==="top"?0:1,i==="top"?-1:0),ue.camera.lookAt(t),zi(),Es(),Zn(),ue.render()}function Zn(){let i=!!(Ht?.available&&Number.isFinite(at?.rawMin)),e=j("world-map-cloud-hud-points"),t=j("world-map-cloud-hud-depth"),n=j("world-map-cloud-hud-age"),r=j("world-map-cloud-hud-sync"),s=j("world-map-cloud-hud-pipeline"),a=j("world-map-cloud-hud-fps");e&&(e.textContent=`${Ju.toLocaleString()} points`),t&&(t.textContent=`MiDaS ${Zt?.latency_ms==null?"\u2014":`${Number(Zt.latency_ms).toFixed(1)} ms`}`);let o=Number(at?.capturedAt)||0,l=o>0?Math.max(0,Date.now()/1e3-o):NaN;if(s){let M=Number(at?.workerReceivedAt)||0,y=Number(at?.publishedAt)||0,C=Number(at?.browserFetchedAt)||0,E=Number(at?.cloudBuiltAt)||0,R=Number(Zt?.inference_ms),P=(w,v)=>`${w} ${Number.isFinite(v)?`${Math.round(v)}ms`:"\u2014"}`;s.textContent=[P("pre",M&&o?Math.max(0,(M-o)*1e3):NaN),P("infer",R),P("svc",M&&y?Math.max(0,(y-M)*1e3):NaN),P("fetch",y&&C?Math.max(0,(C-y)*1e3):NaN),P("build",C&&E?Math.max(0,(E-C)*1e3):NaN)].join(" \xB7 "),s.title="pre: capture to worker acceptance; infer: model inference only; svc: service round-trip to publish; fetch: publish to browser; build: PNG decode and cloud upload."}let c=Number(kt?.captured_at),d=c>0&&o>0?Math.abs(c-o):NaN,u=!Number.isFinite(l)||l>.5||Number.isFinite(d)&&d>.5,h=j("world-map-cloud-stale");if(h&&(h.hidden=!u,h.textContent=Number.isFinite(l)?l>.5?`STALE \xB7 MiDaS frame ${l.toFixed(1)} s old \xB7 last depth frame retained`:`STALE \xB7 camera/depth differ by ${d.toFixed(1)} s \xB7 detections hidden`:"MiDaS frame unavailable"),tt?.material?.uniforms&&(tt.material.uniforms.uOpacity.value=.92),n&&(n.textContent=Number.isFinite(l)?`Frame ${l.toFixed(1)} s`:"Frame \u2014"),r){let M=Number(kt?.captured_at),y=Number(at?.capturedAt),C=M>0&&y>0?Math.abs(M-y):NaN,E=ju===at?.frameId?"camera matched":"depth view",R=String(at?.frameId||"\u2014").slice(-14);r.textContent=Number.isFinite(C)?`D ${R} \xB7 camera \u0394 ${C.toFixed(1)} s \xB7 MiDaS cloud \xB7 ${E}`:`D ${R} \xB7 MiDaS cloud \xB7 ${E}`}let p=performance.now(),g=p-Wu;a&&g>=500&&(a.textContent=`3D ${Math.round(Tc*1e3/g)} FPS`,Tc=0,Wu=p);let x=j("world-map-cloud-depth-caption"),f=ki(at).calibrated?"camera intrinsics calibrated":`camera FOV estimated ${bs.horizontalFovDeg}\xB0`;x&&(x.textContent=i?`Depth in metres \xB7 ${f}; radar remains independent`:`Pseudo-metres \xB7 uncalibrated; shape only, not range \xB7 ${f}`);let S=gt?.querySelector(".world-map-cloud-scale");S&&(S.hidden=!0),Ui&&(Ui.visible=!gt?.classList.contains("is-camera-view")),Oi&&(Oi.visible=!gt?.classList.contains("is-camera-view")),$t&&($t.visible=!!gt?.classList.contains("is-camera-view"))}function xh(){if(!ue||!Uo||!gt||Uo.hidden)return;let i=gt.getBoundingClientRect();if(!i.width||!i.height)return;ue.camera.updateMatrixWorld();let e=[];for(let t of ys){let n=t.position.clone().project(ue.camera),r=t.element,s=n.z>=-1&&n.z<=1&&n.x>=-1.15&&n.x<=1.15&&n.y>=-1.15&&n.y<=1.15;if(r.hidden=!s,!s)continue;let a=yt.clamp((n.x+1)*i.width/2,8,i.width-8);if(t.marker){r.style.left=`${a}px`,r.style.top=`${yt.clamp((1-n.y)*i.height/2,10,i.height-10)}px`;continue}let o=Math.min(r.offsetWidth||150,i.width-16),l=r.offsetHeight||24;a=yt.clamp(a,o/2+8,i.width-o/2-8);let c=yt.clamp((1-n.y)*i.height/2-12,l+8,i.height-8),d=!1;for(let u=0;u<12;u++){let h=Math.ceil(u/2)*(l+5)*(u%2?-1:1),p=yt.clamp(c+h,l+8,i.height-8),g={left:a-o/2,top:p-l,right:a+o/2,bottom:p};if(!e.some(m=>g.left<m.right+4&&g.right>m.left-4&&g.top<m.bottom+3&&g.bottom>m.top-3)){e.push(g),r.style.left=`${a}px`,r.style.top=`${p}px`,d=!0;break}}r.hidden=!d}}function ko(i,e){ys=ys.filter(t=>t.layer!==i);for(let t of e){let n=document.createElement("span");n.className=t.marker?`world-map-cloud-radar-dot${t.motionClass?` ${t.motionClass}`:""}`:"world-map-cloud-object-label",n.textContent=t.text||"",Uo?.append(n),ys.push({...t,layer:i,element:n})}Uo?.querySelectorAll(".world-map-cloud-object-label,.world-map-cloud-radar-dot").forEach(t=>{ys.some(n=>n.element===t)||t.remove()}),xh()}function zi(i=Sn,e=!1){if(!ue)return;let t=gt?.querySelector('[data-cloud-layer="radar"]')?.checked===!0,n=i?.targets||[],r=n.map(u=>{let h=u.position_m||u.position||[];return`${u.id||u.target_id||""}:${h[0]}:${h[1]}:${u.radial_speed_mps}`}).join("|"),s=`${t}:${i?.timestamp||"none"}:${r}:${gt?.classList.contains("is-camera-view")}`;if(!e&&s===Vu)return;Vu=s,_h(vs);let a=[];vs.visible=t;let o=Number(pi?.captured_at)||0,l=Number(i?.timestamp)||0,d=pi?.state==="ready"&&Date.now()/1e3-o<=.5&&Math.abs(o-l)<=.2?zo(nh(pi),i,at).map(u=>u.targetIndex):[];for(let[u,h]of n.entries()){let p=h.position_m||h.position||[],g=Number(p[0]),x=Number(p[1]);if(!Number.isFinite(g)||!Number.isFinite(x)||x<0||x>12)continue;let m=ah(new N(g,0,-x),i.timestamp);Vo(i.timestamp);let f=Number(hn?.captured_at)>0?Date.now()/1e3-Number(hn.captured_at):1/0,S=hn?.available&&f<=.35&&Number(hn.confidence)>=.35&&Number(hn.speed_mps)>=.05,M=Math.abs(Number(h.radial_speed_mps)||0)>=.05&&!S,y=S?"#9aa7ad":M?"#ed35c5":"#f2bc65",C=new st(new li(.11,16,10),new Xt({color:y,transparent:!0,opacity:.24,depthTest:!1,depthWrite:!1}));C.position.copy(m),C.renderOrder=20,vs.add(C);let E=new st(new li(.055,16,12),new Xt({color:y,depthTest:!1,depthWrite:!1}));E.position.copy(m),E.renderOrder=21,vs.add(E),a.push({position:m,marker:!0,motionClass:S?"is-ego-motion":M?"is-moving":""});let R=d.includes(u);a.push({position:m.clone().add(new N(0,.16,0)),text:`${R?"Person \xB7 YOLOX matched":`Radar target ${u+1} \xB7 unassociated`} \xB7 ${x.toFixed(1)} m forward${S?" \xB7 radial motion ego-uncompensated":""}`})}ko("radar",a),Rt==="3d"&&ue.render()}function Es(){if(!ue)return;_h(Ms);let i=gt?.querySelector('[data-cloud-layer="odometry"]')?.checked!==!1&&!gt?.classList.contains("is-camera-view");if(Ms.visible=i,Yn.length<2)return;let e=Ts().heightM,t=Yn.map(r=>new N(-r.lateral,e,-r.forward)),n=new Wn(new dt().setFromPoints(t),new nn({color:"#ed35c5",linewidth:2}));Ms.add(n),ue.render()}function _h(i){for(let e of[...i.children])i.remove(e),e.traverse?.(t=>{t.geometry?.dispose(),t.material?.dispose?.()})}async function Mx(i,e){let t=new Image;t.src=`data:${e};base64,${i}`,await t.decode();let n=document.createElement("canvas");n.width=t.naturalWidth,n.height=t.naturalHeight;let r=n.getContext("2d",{willReadFrequently:!0});return r.drawImage(t,0,0),{width:n.width,height:n.height,values:r.getImageData(0,0,n.width,n.height).data}}var Yu=new Map([[0,"#ef8354"],[3,"#00b4d8"],[5,"#9b5de5"],[12,"#ff4d6d"],[14,"#ff9f1c"],[15,"#ffd166"],[17,"#70e000"],[19,"#00f5d4"],[22,"#e76f51"],[27,"#4361ee"],[89,"#3a86ff"],[130,"#c77dff"],[141,"#fb5607"],[143,"#80ed99"]]);function Zu(i){if(Yu.has(Number(i)))return new Ne(Yu.get(Number(i)));let e=(Number(i)*137.508+18)%360;return new Ne().setHSL(e/360,.72,.58)}function yh(i,e){if(!i?.available||!i.mask_png_base64)return!1;if(i.frame_id&&i.frame_id===e.frame_id)return!0;let t=Number(i.captured_at),n=Number(e.captured_at);return Number.isFinite(t)&&Number.isFinite(n)&&Math.abs(t-n)<=.25}async function Sx(i,e=Cr){if(!ue||!i.depth_gray_jpeg_base64)return;let t=++mc,n=await dh(i);if(t!==mc||ut!=="sensors"||Rt!=="3d")return!1;at=n,ju="",Mc=yh(e,i)?String(e.frame_id||e.captured_at||""):"",Ss=null,mt=Number(i.captured_at)||0,Vo(mt),Ec+=1;let r=Ht;Zn();let s=ki(n),a=Math.max(3,Math.ceil(Math.max(n.width,n.height)/120)),o=[],l=[];for(let u=0;u<n.height;u+=a)for(let h=0;h<n.width;h+=a){let p=(u*n.width+h)*4;if(sh(n,u*n.width+h)<.035)continue;let x=Ac(n,p,r),m=Yt(qt(h,u,x,s),Number(i.captured_at)||mt);o.push(m.x,m.y,m.z),l.push((n.normalizedValues?.[p]??n.values[p])/255)}let c=new dt;c.setAttribute("position",new je(o,3)),c.setAttribute("depthValue",new je(l,1)),c.computeBoundingBox(),Ju=o.length/3;let d=gt?.querySelector('[data-cloud-layer="cloud"]')?.checked!==!1;if(tt){let u=tt.geometry;tt.geometry=c,tt.visible=d,u.dispose()}else tt=new jr(c,mx(Number(j("world-map-cloud-point-size")?.value||25)/1e3)),tt.visible=d,ue.scene.add(tt);return zi(),Es(),Go(),fx(i).then(u=>{let h=at;if(!u||ut!=="sensors"||Rt!=="3d"||!h)return;let p=Math.abs(Number(u.captured_at)-Number(h.capturedAt));if(h!==n&&(!Number.isFinite(p)||p>No))return;let g={...u,frame_delta_s:p};Ss=g,Wo(h,g,Ht)}).catch(u=>console.warn("Could not pair YOLOX with MiDaS frame:",u)),gt?.classList.contains("is-camera-view")&&lh(i).then(u=>t===mc&&u?ch(u):!1).then(()=>ue.render()).catch(u=>console.warn("Could not load camera-aligned 3D background:",u)),n.cloudBuiltAt=Date.now()/1e3,Zn(),ue.render(),Ar=String(i.frame_id||""),!0}function Ex(i,e,t,n){let[r,s,a,o]=e.map(Number),l=/person|human/i.test(n);if(/tv|monitor|screen|television/i.test(n)){let f=Math.max(.015,(a-r)*.12),S=Math.max(.02,(o-s)*.12),M=Math.max(0,Math.floor((r-f)*i.width)),y=Math.min(i.width,Math.ceil((a+f)*i.width)),C=Math.max(0,Math.floor((s-S)*i.height)),E=Math.min(i.height,Math.ceil((o+S)*i.height)),R=Math.max(1,Math.floor(Math.min(y-M,E-C)/16)),P=[];for(let v=C;v<E;v+=R)for(let T=M;T<y;T+=R){let D=T/i.width,F=v/i.height;D>=r&&D<=a&&F>=s&&F<=o||P.push(Ac(i,(v*i.width+T)*4,t))}if(P.sort((v,T)=>v-T),!P.length)return null;let w=v=>P[Math.floor((P.length-1)*v)];return{near:w(.1),median:w(.5),far:w(.9),screen:!0}}let c=l?.25:.15,d=Math.max(0,Math.floor((r+(a-r)*c)*i.width)),u=Math.min(i.width,Math.ceil((a-(a-r)*c)*i.width)),h=Math.max(0,Math.floor((s+(o-s)*(l?.2:.15))*i.height)),p=Math.min(i.height,Math.ceil((s+(o-s)*(l?.72:.85))*i.height)),g=Math.max(1,Math.floor(Math.min(u-d,p-h)/12)),x=[];for(let f=h;f<p;f+=g)for(let S=d;S<u;S+=g)x.push(Ac(i,(f*i.width+S)*4,t));if(x.sort((f,S)=>f-S),!x.length)return null;let m=f=>x[Math.min(x.length-1,Math.floor((x.length-1)*f))];return{near:m(.1),median:m(.5),far:m(.9)}}function Wo(i,e,t=Ht){if(!ue||!i||Rt!=="3d")return;let n=gt?.querySelector('[data-cloud-layer="detections"]')?.checked!==!1,r=e?.frame_delta_s!=null&&Number.isFinite(Number(e.frame_delta_s))?Number(e.frame_delta_s):Math.abs(Number(e?.captured_at)-Number(i.capturedAt)),s=!!(i.frameId&&e?.frame_id===i.frameId)||Number.isFinite(r)&&r<=No,a=n&&s&&e?.state==="ready"&&e?.paired!==!1?cx(e):[],o=`${n}:${Ar}:${e?.frame_id||""}:${a.length}:${Number(mt).toFixed(3)}`;if(o===Hu)return;Hu=o;let l=new Bt,c=[],d=["#55e7cc","#f2bc65","#e280ba","#77d69c"],u=!!(t?.available&&Number.isFinite(i.rawMin)&&Number.isFinite(i.rawMax)),h=s&&u&&r<=.15?tx(mt,.1):null,p=h?zo(a,h,i):[];for(let[g,x]of a.entries()){let m=x.bbox;if(!Array.isArray(m)||m.length<4||!m.every(Fe=>Number.isFinite(Number(Fe))))continue;let[f,S,M,y]=m.map(Number),C=String(x.label||x.class_name||x.class||"object"),E=Ex(i,m,t,C);if(!E)continue;let R=p.find(Fe=>Fe.detection===x),P=s&&u?hx(E.median,t):null,w=R?R.forward:E.median,v=Math.max(0,E.far-E.near),T=u?Math.min(.6,Math.max(.15,w*.3)):Math.min(.35,Math.max(.02,w*.05)),D=E.screen?Math.min(v,u?.04:.02):Math.min(v,T),F=Math.max(.15,w-D/2),B=Math.max(F+(u?.03:.01),w+D/2),k=ki(i),W=[Yt(qt(f*i.width,S*i.height,F,k),mt),Yt(qt(M*i.width,S*i.height,F,k),mt),Yt(qt(M*i.width,y*i.height,F,k),mt),Yt(qt(f*i.width,y*i.height,F,k),mt),Yt(qt(f*i.width,S*i.height,B,k),mt),Yt(qt(M*i.width,S*i.height,B,k),mt),Yt(qt(M*i.width,y*i.height,B,k),mt),Yt(qt(f*i.width,y*i.height,B,k),mt)],X=[0,1,1,2,2,3,3,0,4,5,5,6,6,7,7,4,0,4,1,5,2,6,3,7],H=new nn({color:d[g%d.length],depthTest:!1,transparent:!0,opacity:.95});l.add(new oi(new dt().setFromPoints(X.map(Fe=>W[Fe])),H));let Q=Yt(qt((f+M)*i.width/2,S*i.height,F,k),mt),ne=Math.round(Number(x.confidence??x.score??0)*100),fe=R?`${R.forward.toFixed(2)} m \xB7 radar measured`:P?`${P.extrapolated?"~":""}${P.meters.toFixed(1)} m \xB7 MiDaS ${P.extrapolated?"extrapolated":"est."}`:s?`${E.median.toFixed(1)} pseudo-m \xB7 uncalibrated MiDaS`:"depth unpaired \xB7 relative shape only",De=e?.frame_id!==i.frameId&&r>.15?` \xB7 YOLOX \u0394${r.toFixed(1)} s`:"",Xe=i.capturedAt>0?Math.max(0,Date.now()/1e3-i.capturedAt):1/0,Ze=Xe>1.25?` \xB7 MiDaS stale ${Xe.toFixed(1)} s`:"";c.push({position:Q,text:`${C} ${ne}% \xB7 ${fe}${De}${Ze}`})}fi&&(ue.scene.remove(fi),fi.traverse(g=>{g.geometry?.dispose(),g.material?.dispose?.()})),fi=l,fi.visible=n,ue.scene.add(fi),ko("detections",c),ue.render()}window.updateBodyWorldMap3D=i=>{Bi=i,ut==="simulation"&&Rt==="3d"&&Ho(i)};var Hi=()=>document.visibilityState!=="hidden";setInterval(()=>{Hi()&&ut==="sensors"&&(Ic(),Pc())},100);setInterval(()=>{!Hi()||ut!=="sensors"||hh()},250);setInterval(()=>{Hi()&&_x()},1500);setInterval(()=>{!Hi()||ut!=="sensors"||(fh(),ph(),mh())},500);setInterval(()=>{Hi()&&ut==="sensors"&&yx()},1e3);setInterval(()=>{Hi()&&ut==="sensors"&&vx()},500);document.addEventListener("visibilitychange",()=>{Hi()&&ut==="sensors"&&(Ic(),Pc(),hh(),fh(),ph(),mh())});Bi&&Ho(Bi);})();
/*! Bundled license information:

three/build/three.core.js:
three/build/three.module.js:
  (**
   * @license
   * Copyright 2010-2025 Three.js Authors
   * SPDX-License-Identifier: MIT
   *)
*/
