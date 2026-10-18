(()=>{var md=0,Al=1,gd=2;var Cl=1,xd=2,Pn=3,Gn=0,zt=1,un=2,$n=0,Si=1,Rl=2,Il=3,Pl=4,_d=5,ai=100,yd=101,vd=102,bd=103,wd=104,Md=200,Sd=201,Ed=202,Td=203,aa=204,oa=205,Ad=206,Cd=207,Rd=208,Id=209,Pd=210,Nd=211,Dd=212,Ld=213,Fd=214,Da=0,La=1,Fa=2,Ei=3,Ua=4,Oa=5,Ba=6,za=7,Nl=0,Ud=1,Od=2,qn=0,Bd=1,zd=2,kd=3,Hd=4,Vd=5,Gd=6,Wd=7;var Dl=300,Ri=301,Ii=302,ka=303,Ha=304,fs=306,la=1e3,si=1001,ca=1002,dn=1003,Xd=1004;var ps=1005;var bn=1006,Va=1007;var fi=1008;var Sn=1009,Ll=1010,Fl=1011,_r=1012,Ga=1013,pi=1014,Nn=1015,yr=1016,Wa=1017,Xa=1018,vr=1020,Ul=35902,Ol=35899,Bl=1021,zl=1022,hn=1023,cr=1026,br=1027,kl=1028,$a=1029,Hl=1030,qa=1031;var Ya=1033,ms=33776,gs=33777,xs=33778,_s=33779,Za=35840,Ja=35841,Ka=35842,ja=35843,Qa=36196,eo=37492,to=37496,no=37808,io=37809,ro=37810,so=37811,ao=37812,oo=37813,lo=37814,co=37815,uo=37816,ho=37817,fo=37818,po=37819,mo=37820,go=37821,xo=36492,_o=36494,yo=36495,vo=36283,bo=36284,wo=36285,Mo=36286;var kr=2300,da=2301,sa=2302,yl=2400,vl=2401,bl=2402;var $d=3200,qd=3201;var Vl=0,Yd=1,Yn="",Nt="srgb",Ti="srgb-linear",Hr="linear",tt="srgb";var Mi=7680;var wl=519,Zd=512,Jd=513,Kd=514,Gl=515,jd=516,Qd=517,eu=518,tu=519,ua=35044;var Wl="300 es",vn=2e3,Vr=2001;var Wn=class{addEventListener(e,t){this._listeners===void 0&&(this._listeners={});let n=this._listeners;n[e]===void 0&&(n[e]=[]),n[e].indexOf(t)===-1&&n[e].push(t)}hasEventListener(e,t){let n=this._listeners;return n===void 0?!1:n[e]!==void 0&&n[e].indexOf(t)!==-1}removeEventListener(e,t){let n=this._listeners;if(n===void 0)return;let r=n[e];if(r!==void 0){let s=r.indexOf(t);s!==-1&&r.splice(s,1)}}dispatchEvent(e){let t=this._listeners;if(t===void 0)return;let n=t[e.type];if(n!==void 0){e.target=this;let r=n.slice(0);for(let s=0,a=r.length;s<a;s++)r[s].call(this,e);e.target=null}}},It=["00","01","02","03","04","05","06","07","08","09","0a","0b","0c","0d","0e","0f","10","11","12","13","14","15","16","17","18","19","1a","1b","1c","1d","1e","1f","20","21","22","23","24","25","26","27","28","29","2a","2b","2c","2d","2e","2f","30","31","32","33","34","35","36","37","38","39","3a","3b","3c","3d","3e","3f","40","41","42","43","44","45","46","47","48","49","4a","4b","4c","4d","4e","4f","50","51","52","53","54","55","56","57","58","59","5a","5b","5c","5d","5e","5f","60","61","62","63","64","65","66","67","68","69","6a","6b","6c","6d","6e","6f","70","71","72","73","74","75","76","77","78","79","7a","7b","7c","7d","7e","7f","80","81","82","83","84","85","86","87","88","89","8a","8b","8c","8d","8e","8f","90","91","92","93","94","95","96","97","98","99","9a","9b","9c","9d","9e","9f","a0","a1","a2","a3","a4","a5","a6","a7","a8","a9","aa","ab","ac","ad","ae","af","b0","b1","b2","b3","b4","b5","b6","b7","b8","b9","ba","bb","bc","bd","be","bf","c0","c1","c2","c3","c4","c5","c6","c7","c8","c9","ca","cb","cc","cd","ce","cf","d0","d1","d2","d3","d4","d5","d6","d7","d8","d9","da","db","dc","dd","de","df","e0","e1","e2","e3","e4","e5","e6","e7","e8","e9","ea","eb","ec","ed","ee","ef","f0","f1","f2","f3","f4","f5","f6","f7","f8","f9","fa","fb","fc","fd","fe","ff"],kc=1234567,or=Math.PI/180,dr=180/Math.PI;function Hn(){let i=Math.random()*4294967295|0,e=Math.random()*4294967295|0,t=Math.random()*4294967295|0,n=Math.random()*4294967295|0;return(It[i&255]+It[i>>8&255]+It[i>>16&255]+It[i>>24&255]+"-"+It[e&255]+It[e>>8&255]+"-"+It[e>>16&15|64]+It[e>>24&255]+"-"+It[t&63|128]+It[t>>8&255]+"-"+It[t>>16&255]+It[t>>24&255]+It[n&255]+It[n>>8&255]+It[n>>16&255]+It[n>>24&255]).toLowerCase()}function Ye(i,e,t){return Math.max(e,Math.min(t,i))}function Xl(i,e){return(i%e+e)%e}function Rh(i,e,t,n,r){return n+(i-e)*(r-n)/(t-e)}function Ih(i,e,t){return i!==e?(t-i)/(e-i):0}function zr(i,e,t){return(1-t)*i+t*e}function Ph(i,e,t,n){return zr(i,e,1-Math.exp(-t*n))}function Nh(i,e=1){return e-Math.abs(Xl(i,e*2)-e)}function Dh(i,e,t){return i<=e?0:i>=t?1:(i=(i-e)/(t-e),i*i*(3-2*i))}function Lh(i,e,t){return i<=e?0:i>=t?1:(i=(i-e)/(t-e),i*i*i*(i*(i*6-15)+10))}function Fh(i,e){return i+Math.floor(Math.random()*(e-i+1))}function Uh(i,e){return i+Math.random()*(e-i)}function Oh(i){return i*(.5-Math.random())}function Bh(i){i!==void 0&&(kc=i);let e=kc+=1831565813;return e=Math.imul(e^e>>>15,e|1),e^=e+Math.imul(e^e>>>7,e|61),((e^e>>>14)>>>0)/4294967296}function zh(i){return i*or}function kh(i){return i*dr}function Hh(i){return(i&i-1)===0&&i!==0}function Vh(i){return Math.pow(2,Math.ceil(Math.log(i)/Math.LN2))}function Gh(i){return Math.pow(2,Math.floor(Math.log(i)/Math.LN2))}function Wh(i,e,t,n,r){let s=Math.cos,a=Math.sin,o=s(t/2),c=a(t/2),l=s((e+n)/2),u=a((e+n)/2),d=s((e-n)/2),h=a((e-n)/2),p=s((n-e)/2),g=a((n-e)/2);switch(r){case"XYX":i.set(o*u,c*d,c*h,o*l);break;case"YZY":i.set(c*h,o*u,c*d,o*l);break;case"ZXZ":i.set(c*d,c*h,o*u,o*l);break;case"XZX":i.set(o*u,c*g,c*p,o*l);break;case"YXY":i.set(c*p,o*u,c*g,o*l);break;case"ZYZ":i.set(c*g,c*p,o*u,o*l);break;default:console.warn("THREE.MathUtils: .setQuaternionFromProperEuler() encountered an unknown order: "+r)}}function yn(i,e){switch(e.constructor){case Float32Array:return i;case Uint32Array:return i/4294967295;case Uint16Array:return i/65535;case Uint8Array:return i/255;case Int32Array:return Math.max(i/2147483647,-1);case Int16Array:return Math.max(i/32767,-1);case Int8Array:return Math.max(i/127,-1);default:throw new Error("Invalid component type.")}}function et(i,e){switch(e.constructor){case Float32Array:return i;case Uint32Array:return Math.round(i*4294967295);case Uint16Array:return Math.round(i*65535);case Uint8Array:return Math.round(i*255);case Int32Array:return Math.round(i*2147483647);case Int16Array:return Math.round(i*32767);case Int8Array:return Math.round(i*127);default:throw new Error("Invalid component type.")}}var bt={DEG2RAD:or,RAD2DEG:dr,generateUUID:Hn,clamp:Ye,euclideanModulo:Xl,mapLinear:Rh,inverseLerp:Ih,lerp:zr,damp:Ph,pingpong:Nh,smoothstep:Dh,smootherstep:Lh,randInt:Fh,randFloat:Uh,randFloatSpread:Oh,seededRandom:Bh,degToRad:zh,radToDeg:kh,isPowerOfTwo:Hh,ceilPowerOfTwo:Vh,floorPowerOfTwo:Gh,setQuaternionFromProperEuler:Wh,normalize:et,denormalize:yn},We=class i{constructor(e=0,t=0){i.prototype.isVector2=!0,this.x=e,this.y=t}get width(){return this.x}set width(e){this.x=e}get height(){return this.y}set height(e){this.y=e}set(e,t){return this.x=e,this.y=t,this}setScalar(e){return this.x=e,this.y=e,this}setX(e){return this.x=e,this}setY(e){return this.y=e,this}setComponent(e,t){switch(e){case 0:this.x=t;break;case 1:this.y=t;break;default:throw new Error("index is out of range: "+e)}return this}getComponent(e){switch(e){case 0:return this.x;case 1:return this.y;default:throw new Error("index is out of range: "+e)}}clone(){return new this.constructor(this.x,this.y)}copy(e){return this.x=e.x,this.y=e.y,this}add(e){return this.x+=e.x,this.y+=e.y,this}addScalar(e){return this.x+=e,this.y+=e,this}addVectors(e,t){return this.x=e.x+t.x,this.y=e.y+t.y,this}addScaledVector(e,t){return this.x+=e.x*t,this.y+=e.y*t,this}sub(e){return this.x-=e.x,this.y-=e.y,this}subScalar(e){return this.x-=e,this.y-=e,this}subVectors(e,t){return this.x=e.x-t.x,this.y=e.y-t.y,this}multiply(e){return this.x*=e.x,this.y*=e.y,this}multiplyScalar(e){return this.x*=e,this.y*=e,this}divide(e){return this.x/=e.x,this.y/=e.y,this}divideScalar(e){return this.multiplyScalar(1/e)}applyMatrix3(e){let t=this.x,n=this.y,r=e.elements;return this.x=r[0]*t+r[3]*n+r[6],this.y=r[1]*t+r[4]*n+r[7],this}min(e){return this.x=Math.min(this.x,e.x),this.y=Math.min(this.y,e.y),this}max(e){return this.x=Math.max(this.x,e.x),this.y=Math.max(this.y,e.y),this}clamp(e,t){return this.x=Ye(this.x,e.x,t.x),this.y=Ye(this.y,e.y,t.y),this}clampScalar(e,t){return this.x=Ye(this.x,e,t),this.y=Ye(this.y,e,t),this}clampLength(e,t){let n=this.length();return this.divideScalar(n||1).multiplyScalar(Ye(n,e,t))}floor(){return this.x=Math.floor(this.x),this.y=Math.floor(this.y),this}ceil(){return this.x=Math.ceil(this.x),this.y=Math.ceil(this.y),this}round(){return this.x=Math.round(this.x),this.y=Math.round(this.y),this}roundToZero(){return this.x=Math.trunc(this.x),this.y=Math.trunc(this.y),this}negate(){return this.x=-this.x,this.y=-this.y,this}dot(e){return this.x*e.x+this.y*e.y}cross(e){return this.x*e.y-this.y*e.x}lengthSq(){return this.x*this.x+this.y*this.y}length(){return Math.sqrt(this.x*this.x+this.y*this.y)}manhattanLength(){return Math.abs(this.x)+Math.abs(this.y)}normalize(){return this.divideScalar(this.length()||1)}angle(){return Math.atan2(-this.y,-this.x)+Math.PI}angleTo(e){let t=Math.sqrt(this.lengthSq()*e.lengthSq());if(t===0)return Math.PI/2;let n=this.dot(e)/t;return Math.acos(Ye(n,-1,1))}distanceTo(e){return Math.sqrt(this.distanceToSquared(e))}distanceToSquared(e){let t=this.x-e.x,n=this.y-e.y;return t*t+n*n}manhattanDistanceTo(e){return Math.abs(this.x-e.x)+Math.abs(this.y-e.y)}setLength(e){return this.normalize().multiplyScalar(e)}lerp(e,t){return this.x+=(e.x-this.x)*t,this.y+=(e.y-this.y)*t,this}lerpVectors(e,t,n){return this.x=e.x+(t.x-e.x)*n,this.y=e.y+(t.y-e.y)*n,this}equals(e){return e.x===this.x&&e.y===this.y}fromArray(e,t=0){return this.x=e[t],this.y=e[t+1],this}toArray(e=[],t=0){return e[t]=this.x,e[t+1]=this.y,e}fromBufferAttribute(e,t){return this.x=e.getX(t),this.y=e.getY(t),this}rotateAround(e,t){let n=Math.cos(t),r=Math.sin(t),s=this.x-e.x,a=this.y-e.y;return this.x=s*n-a*r+e.x,this.y=s*r+a*n+e.y,this}random(){return this.x=Math.random(),this.y=Math.random(),this}*[Symbol.iterator](){yield this.x,yield this.y}},Gt=class{constructor(e=0,t=0,n=0,r=1){this.isQuaternion=!0,this._x=e,this._y=t,this._z=n,this._w=r}static slerpFlat(e,t,n,r,s,a,o){let c=n[r+0],l=n[r+1],u=n[r+2],d=n[r+3],h=s[a+0],p=s[a+1],g=s[a+2],x=s[a+3];if(o===0){e[t+0]=c,e[t+1]=l,e[t+2]=u,e[t+3]=d;return}if(o===1){e[t+0]=h,e[t+1]=p,e[t+2]=g,e[t+3]=x;return}if(d!==x||c!==h||l!==p||u!==g){let m=1-o,f=c*h+l*p+u*g+d*x,S=f>=0?1:-1,M=1-f*f;if(M>Number.EPSILON){let C=Math.sqrt(M),A=Math.atan2(C,f*S);m=Math.sin(m*A)/C,o=Math.sin(o*A)/C}let y=o*S;if(c=c*m+h*y,l=l*m+p*y,u=u*m+g*y,d=d*m+x*y,m===1-o){let C=1/Math.sqrt(c*c+l*l+u*u+d*d);c*=C,l*=C,u*=C,d*=C}}e[t]=c,e[t+1]=l,e[t+2]=u,e[t+3]=d}static multiplyQuaternionsFlat(e,t,n,r,s,a){let o=n[r],c=n[r+1],l=n[r+2],u=n[r+3],d=s[a],h=s[a+1],p=s[a+2],g=s[a+3];return e[t]=o*g+u*d+c*p-l*h,e[t+1]=c*g+u*h+l*d-o*p,e[t+2]=l*g+u*p+o*h-c*d,e[t+3]=u*g-o*d-c*h-l*p,e}get x(){return this._x}set x(e){this._x=e,this._onChangeCallback()}get y(){return this._y}set y(e){this._y=e,this._onChangeCallback()}get z(){return this._z}set z(e){this._z=e,this._onChangeCallback()}get w(){return this._w}set w(e){this._w=e,this._onChangeCallback()}set(e,t,n,r){return this._x=e,this._y=t,this._z=n,this._w=r,this._onChangeCallback(),this}clone(){return new this.constructor(this._x,this._y,this._z,this._w)}copy(e){return this._x=e.x,this._y=e.y,this._z=e.z,this._w=e.w,this._onChangeCallback(),this}setFromEuler(e,t=!0){let n=e._x,r=e._y,s=e._z,a=e._order,o=Math.cos,c=Math.sin,l=o(n/2),u=o(r/2),d=o(s/2),h=c(n/2),p=c(r/2),g=c(s/2);switch(a){case"XYZ":this._x=h*u*d+l*p*g,this._y=l*p*d-h*u*g,this._z=l*u*g+h*p*d,this._w=l*u*d-h*p*g;break;case"YXZ":this._x=h*u*d+l*p*g,this._y=l*p*d-h*u*g,this._z=l*u*g-h*p*d,this._w=l*u*d+h*p*g;break;case"ZXY":this._x=h*u*d-l*p*g,this._y=l*p*d+h*u*g,this._z=l*u*g+h*p*d,this._w=l*u*d-h*p*g;break;case"ZYX":this._x=h*u*d-l*p*g,this._y=l*p*d+h*u*g,this._z=l*u*g-h*p*d,this._w=l*u*d+h*p*g;break;case"YZX":this._x=h*u*d+l*p*g,this._y=l*p*d+h*u*g,this._z=l*u*g-h*p*d,this._w=l*u*d-h*p*g;break;case"XZY":this._x=h*u*d-l*p*g,this._y=l*p*d-h*u*g,this._z=l*u*g+h*p*d,this._w=l*u*d+h*p*g;break;default:console.warn("THREE.Quaternion: .setFromEuler() encountered an unknown order: "+a)}return t===!0&&this._onChangeCallback(),this}setFromAxisAngle(e,t){let n=t/2,r=Math.sin(n);return this._x=e.x*r,this._y=e.y*r,this._z=e.z*r,this._w=Math.cos(n),this._onChangeCallback(),this}setFromRotationMatrix(e){let t=e.elements,n=t[0],r=t[4],s=t[8],a=t[1],o=t[5],c=t[9],l=t[2],u=t[6],d=t[10],h=n+o+d;if(h>0){let p=.5/Math.sqrt(h+1);this._w=.25/p,this._x=(u-c)*p,this._y=(s-l)*p,this._z=(a-r)*p}else if(n>o&&n>d){let p=2*Math.sqrt(1+n-o-d);this._w=(u-c)/p,this._x=.25*p,this._y=(r+a)/p,this._z=(s+l)/p}else if(o>d){let p=2*Math.sqrt(1+o-n-d);this._w=(s-l)/p,this._x=(r+a)/p,this._y=.25*p,this._z=(c+u)/p}else{let p=2*Math.sqrt(1+d-n-o);this._w=(a-r)/p,this._x=(s+l)/p,this._y=(c+u)/p,this._z=.25*p}return this._onChangeCallback(),this}setFromUnitVectors(e,t){let n=e.dot(t)+1;return n<1e-8?(n=0,Math.abs(e.x)>Math.abs(e.z)?(this._x=-e.y,this._y=e.x,this._z=0,this._w=n):(this._x=0,this._y=-e.z,this._z=e.y,this._w=n)):(this._x=e.y*t.z-e.z*t.y,this._y=e.z*t.x-e.x*t.z,this._z=e.x*t.y-e.y*t.x,this._w=n),this.normalize()}angleTo(e){return 2*Math.acos(Math.abs(Ye(this.dot(e),-1,1)))}rotateTowards(e,t){let n=this.angleTo(e);if(n===0)return this;let r=Math.min(1,t/n);return this.slerp(e,r),this}identity(){return this.set(0,0,0,1)}invert(){return this.conjugate()}conjugate(){return this._x*=-1,this._y*=-1,this._z*=-1,this._onChangeCallback(),this}dot(e){return this._x*e._x+this._y*e._y+this._z*e._z+this._w*e._w}lengthSq(){return this._x*this._x+this._y*this._y+this._z*this._z+this._w*this._w}length(){return Math.sqrt(this._x*this._x+this._y*this._y+this._z*this._z+this._w*this._w)}normalize(){let e=this.length();return e===0?(this._x=0,this._y=0,this._z=0,this._w=1):(e=1/e,this._x=this._x*e,this._y=this._y*e,this._z=this._z*e,this._w=this._w*e),this._onChangeCallback(),this}multiply(e){return this.multiplyQuaternions(this,e)}premultiply(e){return this.multiplyQuaternions(e,this)}multiplyQuaternions(e,t){let n=e._x,r=e._y,s=e._z,a=e._w,o=t._x,c=t._y,l=t._z,u=t._w;return this._x=n*u+a*o+r*l-s*c,this._y=r*u+a*c+s*o-n*l,this._z=s*u+a*l+n*c-r*o,this._w=a*u-n*o-r*c-s*l,this._onChangeCallback(),this}slerp(e,t){if(t===0)return this;if(t===1)return this.copy(e);let n=this._x,r=this._y,s=this._z,a=this._w,o=a*e._w+n*e._x+r*e._y+s*e._z;if(o<0?(this._w=-e._w,this._x=-e._x,this._y=-e._y,this._z=-e._z,o=-o):this.copy(e),o>=1)return this._w=a,this._x=n,this._y=r,this._z=s,this;let c=1-o*o;if(c<=Number.EPSILON){let p=1-t;return this._w=p*a+t*this._w,this._x=p*n+t*this._x,this._y=p*r+t*this._y,this._z=p*s+t*this._z,this.normalize(),this}let l=Math.sqrt(c),u=Math.atan2(l,o),d=Math.sin((1-t)*u)/l,h=Math.sin(t*u)/l;return this._w=a*d+this._w*h,this._x=n*d+this._x*h,this._y=r*d+this._y*h,this._z=s*d+this._z*h,this._onChangeCallback(),this}slerpQuaternions(e,t,n){return this.copy(e).slerp(t,n)}random(){let e=2*Math.PI*Math.random(),t=2*Math.PI*Math.random(),n=Math.random(),r=Math.sqrt(1-n),s=Math.sqrt(n);return this.set(r*Math.sin(e),r*Math.cos(e),s*Math.sin(t),s*Math.cos(t))}equals(e){return e._x===this._x&&e._y===this._y&&e._z===this._z&&e._w===this._w}fromArray(e,t=0){return this._x=e[t],this._y=e[t+1],this._z=e[t+2],this._w=e[t+3],this._onChangeCallback(),this}toArray(e=[],t=0){return e[t]=this._x,e[t+1]=this._y,e[t+2]=this._z,e[t+3]=this._w,e}fromBufferAttribute(e,t){return this._x=e.getX(t),this._y=e.getY(t),this._z=e.getZ(t),this._w=e.getW(t),this._onChangeCallback(),this}toJSON(){return this.toArray()}_onChange(e){return this._onChangeCallback=e,this}_onChangeCallback(){}*[Symbol.iterator](){yield this._x,yield this._y,yield this._z,yield this._w}},D=class i{constructor(e=0,t=0,n=0){i.prototype.isVector3=!0,this.x=e,this.y=t,this.z=n}set(e,t,n){return n===void 0&&(n=this.z),this.x=e,this.y=t,this.z=n,this}setScalar(e){return this.x=e,this.y=e,this.z=e,this}setX(e){return this.x=e,this}setY(e){return this.y=e,this}setZ(e){return this.z=e,this}setComponent(e,t){switch(e){case 0:this.x=t;break;case 1:this.y=t;break;case 2:this.z=t;break;default:throw new Error("index is out of range: "+e)}return this}getComponent(e){switch(e){case 0:return this.x;case 1:return this.y;case 2:return this.z;default:throw new Error("index is out of range: "+e)}}clone(){return new this.constructor(this.x,this.y,this.z)}copy(e){return this.x=e.x,this.y=e.y,this.z=e.z,this}add(e){return this.x+=e.x,this.y+=e.y,this.z+=e.z,this}addScalar(e){return this.x+=e,this.y+=e,this.z+=e,this}addVectors(e,t){return this.x=e.x+t.x,this.y=e.y+t.y,this.z=e.z+t.z,this}addScaledVector(e,t){return this.x+=e.x*t,this.y+=e.y*t,this.z+=e.z*t,this}sub(e){return this.x-=e.x,this.y-=e.y,this.z-=e.z,this}subScalar(e){return this.x-=e,this.y-=e,this.z-=e,this}subVectors(e,t){return this.x=e.x-t.x,this.y=e.y-t.y,this.z=e.z-t.z,this}multiply(e){return this.x*=e.x,this.y*=e.y,this.z*=e.z,this}multiplyScalar(e){return this.x*=e,this.y*=e,this.z*=e,this}multiplyVectors(e,t){return this.x=e.x*t.x,this.y=e.y*t.y,this.z=e.z*t.z,this}applyEuler(e){return this.applyQuaternion(Hc.setFromEuler(e))}applyAxisAngle(e,t){return this.applyQuaternion(Hc.setFromAxisAngle(e,t))}applyMatrix3(e){let t=this.x,n=this.y,r=this.z,s=e.elements;return this.x=s[0]*t+s[3]*n+s[6]*r,this.y=s[1]*t+s[4]*n+s[7]*r,this.z=s[2]*t+s[5]*n+s[8]*r,this}applyNormalMatrix(e){return this.applyMatrix3(e).normalize()}applyMatrix4(e){let t=this.x,n=this.y,r=this.z,s=e.elements,a=1/(s[3]*t+s[7]*n+s[11]*r+s[15]);return this.x=(s[0]*t+s[4]*n+s[8]*r+s[12])*a,this.y=(s[1]*t+s[5]*n+s[9]*r+s[13])*a,this.z=(s[2]*t+s[6]*n+s[10]*r+s[14])*a,this}applyQuaternion(e){let t=this.x,n=this.y,r=this.z,s=e.x,a=e.y,o=e.z,c=e.w,l=2*(a*r-o*n),u=2*(o*t-s*r),d=2*(s*n-a*t);return this.x=t+c*l+a*d-o*u,this.y=n+c*u+o*l-s*d,this.z=r+c*d+s*u-a*l,this}project(e){return this.applyMatrix4(e.matrixWorldInverse).applyMatrix4(e.projectionMatrix)}unproject(e){return this.applyMatrix4(e.projectionMatrixInverse).applyMatrix4(e.matrixWorld)}transformDirection(e){let t=this.x,n=this.y,r=this.z,s=e.elements;return this.x=s[0]*t+s[4]*n+s[8]*r,this.y=s[1]*t+s[5]*n+s[9]*r,this.z=s[2]*t+s[6]*n+s[10]*r,this.normalize()}divide(e){return this.x/=e.x,this.y/=e.y,this.z/=e.z,this}divideScalar(e){return this.multiplyScalar(1/e)}min(e){return this.x=Math.min(this.x,e.x),this.y=Math.min(this.y,e.y),this.z=Math.min(this.z,e.z),this}max(e){return this.x=Math.max(this.x,e.x),this.y=Math.max(this.y,e.y),this.z=Math.max(this.z,e.z),this}clamp(e,t){return this.x=Ye(this.x,e.x,t.x),this.y=Ye(this.y,e.y,t.y),this.z=Ye(this.z,e.z,t.z),this}clampScalar(e,t){return this.x=Ye(this.x,e,t),this.y=Ye(this.y,e,t),this.z=Ye(this.z,e,t),this}clampLength(e,t){let n=this.length();return this.divideScalar(n||1).multiplyScalar(Ye(n,e,t))}floor(){return this.x=Math.floor(this.x),this.y=Math.floor(this.y),this.z=Math.floor(this.z),this}ceil(){return this.x=Math.ceil(this.x),this.y=Math.ceil(this.y),this.z=Math.ceil(this.z),this}round(){return this.x=Math.round(this.x),this.y=Math.round(this.y),this.z=Math.round(this.z),this}roundToZero(){return this.x=Math.trunc(this.x),this.y=Math.trunc(this.y),this.z=Math.trunc(this.z),this}negate(){return this.x=-this.x,this.y=-this.y,this.z=-this.z,this}dot(e){return this.x*e.x+this.y*e.y+this.z*e.z}lengthSq(){return this.x*this.x+this.y*this.y+this.z*this.z}length(){return Math.sqrt(this.x*this.x+this.y*this.y+this.z*this.z)}manhattanLength(){return Math.abs(this.x)+Math.abs(this.y)+Math.abs(this.z)}normalize(){return this.divideScalar(this.length()||1)}setLength(e){return this.normalize().multiplyScalar(e)}lerp(e,t){return this.x+=(e.x-this.x)*t,this.y+=(e.y-this.y)*t,this.z+=(e.z-this.z)*t,this}lerpVectors(e,t,n){return this.x=e.x+(t.x-e.x)*n,this.y=e.y+(t.y-e.y)*n,this.z=e.z+(t.z-e.z)*n,this}cross(e){return this.crossVectors(this,e)}crossVectors(e,t){let n=e.x,r=e.y,s=e.z,a=t.x,o=t.y,c=t.z;return this.x=r*c-s*o,this.y=s*a-n*c,this.z=n*o-r*a,this}projectOnVector(e){let t=e.lengthSq();if(t===0)return this.set(0,0,0);let n=e.dot(this)/t;return this.copy(e).multiplyScalar(n)}projectOnPlane(e){return qo.copy(this).projectOnVector(e),this.sub(qo)}reflect(e){return this.sub(qo.copy(e).multiplyScalar(2*this.dot(e)))}angleTo(e){let t=Math.sqrt(this.lengthSq()*e.lengthSq());if(t===0)return Math.PI/2;let n=this.dot(e)/t;return Math.acos(Ye(n,-1,1))}distanceTo(e){return Math.sqrt(this.distanceToSquared(e))}distanceToSquared(e){let t=this.x-e.x,n=this.y-e.y,r=this.z-e.z;return t*t+n*n+r*r}manhattanDistanceTo(e){return Math.abs(this.x-e.x)+Math.abs(this.y-e.y)+Math.abs(this.z-e.z)}setFromSpherical(e){return this.setFromSphericalCoords(e.radius,e.phi,e.theta)}setFromSphericalCoords(e,t,n){let r=Math.sin(t)*e;return this.x=r*Math.sin(n),this.y=Math.cos(t)*e,this.z=r*Math.cos(n),this}setFromCylindrical(e){return this.setFromCylindricalCoords(e.radius,e.theta,e.y)}setFromCylindricalCoords(e,t,n){return this.x=e*Math.sin(t),this.y=n,this.z=e*Math.cos(t),this}setFromMatrixPosition(e){let t=e.elements;return this.x=t[12],this.y=t[13],this.z=t[14],this}setFromMatrixScale(e){let t=this.setFromMatrixColumn(e,0).length(),n=this.setFromMatrixColumn(e,1).length(),r=this.setFromMatrixColumn(e,2).length();return this.x=t,this.y=n,this.z=r,this}setFromMatrixColumn(e,t){return this.fromArray(e.elements,t*4)}setFromMatrix3Column(e,t){return this.fromArray(e.elements,t*3)}setFromEuler(e){return this.x=e._x,this.y=e._y,this.z=e._z,this}setFromColor(e){return this.x=e.r,this.y=e.g,this.z=e.b,this}equals(e){return e.x===this.x&&e.y===this.y&&e.z===this.z}fromArray(e,t=0){return this.x=e[t],this.y=e[t+1],this.z=e[t+2],this}toArray(e=[],t=0){return e[t]=this.x,e[t+1]=this.y,e[t+2]=this.z,e}fromBufferAttribute(e,t){return this.x=e.getX(t),this.y=e.getY(t),this.z=e.getZ(t),this}random(){return this.x=Math.random(),this.y=Math.random(),this.z=Math.random(),this}randomDirection(){let e=Math.random()*Math.PI*2,t=Math.random()*2-1,n=Math.sqrt(1-t*t);return this.x=n*Math.cos(e),this.y=t,this.z=n*Math.sin(e),this}*[Symbol.iterator](){yield this.x,yield this.y,yield this.z}},qo=new D,Hc=new Gt,ke=class i{constructor(e,t,n,r,s,a,o,c,l){i.prototype.isMatrix3=!0,this.elements=[1,0,0,0,1,0,0,0,1],e!==void 0&&this.set(e,t,n,r,s,a,o,c,l)}set(e,t,n,r,s,a,o,c,l){let u=this.elements;return u[0]=e,u[1]=r,u[2]=o,u[3]=t,u[4]=s,u[5]=c,u[6]=n,u[7]=a,u[8]=l,this}identity(){return this.set(1,0,0,0,1,0,0,0,1),this}copy(e){let t=this.elements,n=e.elements;return t[0]=n[0],t[1]=n[1],t[2]=n[2],t[3]=n[3],t[4]=n[4],t[5]=n[5],t[6]=n[6],t[7]=n[7],t[8]=n[8],this}extractBasis(e,t,n){return e.setFromMatrix3Column(this,0),t.setFromMatrix3Column(this,1),n.setFromMatrix3Column(this,2),this}setFromMatrix4(e){let t=e.elements;return this.set(t[0],t[4],t[8],t[1],t[5],t[9],t[2],t[6],t[10]),this}multiply(e){return this.multiplyMatrices(this,e)}premultiply(e){return this.multiplyMatrices(e,this)}multiplyMatrices(e,t){let n=e.elements,r=t.elements,s=this.elements,a=n[0],o=n[3],c=n[6],l=n[1],u=n[4],d=n[7],h=n[2],p=n[5],g=n[8],x=r[0],m=r[3],f=r[6],S=r[1],M=r[4],y=r[7],C=r[2],A=r[5],I=r[8];return s[0]=a*x+o*S+c*C,s[3]=a*m+o*M+c*A,s[6]=a*f+o*y+c*I,s[1]=l*x+u*S+d*C,s[4]=l*m+u*M+d*A,s[7]=l*f+u*y+d*I,s[2]=h*x+p*S+g*C,s[5]=h*m+p*M+g*A,s[8]=h*f+p*y+g*I,this}multiplyScalar(e){let t=this.elements;return t[0]*=e,t[3]*=e,t[6]*=e,t[1]*=e,t[4]*=e,t[7]*=e,t[2]*=e,t[5]*=e,t[8]*=e,this}determinant(){let e=this.elements,t=e[0],n=e[1],r=e[2],s=e[3],a=e[4],o=e[5],c=e[6],l=e[7],u=e[8];return t*a*u-t*o*l-n*s*u+n*o*c+r*s*l-r*a*c}invert(){let e=this.elements,t=e[0],n=e[1],r=e[2],s=e[3],a=e[4],o=e[5],c=e[6],l=e[7],u=e[8],d=u*a-o*l,h=o*c-u*s,p=l*s-a*c,g=t*d+n*h+r*p;if(g===0)return this.set(0,0,0,0,0,0,0,0,0);let x=1/g;return e[0]=d*x,e[1]=(r*l-u*n)*x,e[2]=(o*n-r*a)*x,e[3]=h*x,e[4]=(u*t-r*c)*x,e[5]=(r*s-o*t)*x,e[6]=p*x,e[7]=(n*c-l*t)*x,e[8]=(a*t-n*s)*x,this}transpose(){let e,t=this.elements;return e=t[1],t[1]=t[3],t[3]=e,e=t[2],t[2]=t[6],t[6]=e,e=t[5],t[5]=t[7],t[7]=e,this}getNormalMatrix(e){return this.setFromMatrix4(e).invert().transpose()}transposeIntoArray(e){let t=this.elements;return e[0]=t[0],e[1]=t[3],e[2]=t[6],e[3]=t[1],e[4]=t[4],e[5]=t[7],e[6]=t[2],e[7]=t[5],e[8]=t[8],this}setUvTransform(e,t,n,r,s,a,o){let c=Math.cos(s),l=Math.sin(s);return this.set(n*c,n*l,-n*(c*a+l*o)+a+e,-r*l,r*c,-r*(-l*a+c*o)+o+t,0,0,1),this}scale(e,t){return this.premultiply(Yo.makeScale(e,t)),this}rotate(e){return this.premultiply(Yo.makeRotation(-e)),this}translate(e,t){return this.premultiply(Yo.makeTranslation(e,t)),this}makeTranslation(e,t){return e.isVector2?this.set(1,0,e.x,0,1,e.y,0,0,1):this.set(1,0,e,0,1,t,0,0,1),this}makeRotation(e){let t=Math.cos(e),n=Math.sin(e);return this.set(t,-n,0,n,t,0,0,0,1),this}makeScale(e,t){return this.set(e,0,0,0,t,0,0,0,1),this}equals(e){let t=this.elements,n=e.elements;for(let r=0;r<9;r++)if(t[r]!==n[r])return!1;return!0}fromArray(e,t=0){for(let n=0;n<9;n++)this.elements[n]=e[n+t];return this}toArray(e=[],t=0){let n=this.elements;return e[t]=n[0],e[t+1]=n[1],e[t+2]=n[2],e[t+3]=n[3],e[t+4]=n[4],e[t+5]=n[5],e[t+6]=n[6],e[t+7]=n[7],e[t+8]=n[8],e}clone(){return new this.constructor().fromArray(this.elements)}},Yo=new ke;function $l(i){for(let e=i.length-1;e>=0;--e)if(i[e]>=65535)return!0;return!1}function Gr(i){return document.createElementNS("http://www.w3.org/1999/xhtml",i)}function nu(){let i=Gr("canvas");return i.style.display="block",i}var Vc={};function ur(i){i in Vc||(Vc[i]=!0,console.warn(i))}function iu(i,e,t){return new Promise(function(n,r){function s(){switch(i.clientWaitSync(e,i.SYNC_FLUSH_COMMANDS_BIT,0)){case i.WAIT_FAILED:r();break;case i.TIMEOUT_EXPIRED:setTimeout(s,t);break;default:n()}}setTimeout(s,t)})}var Gc=new ke().set(.4123908,.3575843,.1804808,.212639,.7151687,.0721923,.0193308,.1191948,.9505322),Wc=new ke().set(3.2409699,-1.5373832,-.4986108,-.9692436,1.8759675,.0415551,.0556301,-.203977,1.0569715);function Xh(){let i={enabled:!0,workingColorSpace:Ti,spaces:{},convert:function(r,s,a){return this.enabled===!1||s===a||!s||!a||(this.spaces[s].transfer===tt&&(r.r=Vn(r.r),r.g=Vn(r.g),r.b=Vn(r.b)),this.spaces[s].primaries!==this.spaces[a].primaries&&(r.applyMatrix3(this.spaces[s].toXYZ),r.applyMatrix3(this.spaces[a].fromXYZ)),this.spaces[a].transfer===tt&&(r.r=lr(r.r),r.g=lr(r.g),r.b=lr(r.b))),r},workingToColorSpace:function(r,s){return this.convert(r,this.workingColorSpace,s)},colorSpaceToWorking:function(r,s){return this.convert(r,s,this.workingColorSpace)},getPrimaries:function(r){return this.spaces[r].primaries},getTransfer:function(r){return r===Yn?Hr:this.spaces[r].transfer},getToneMappingMode:function(r){return this.spaces[r].outputColorSpaceConfig.toneMappingMode||"standard"},getLuminanceCoefficients:function(r,s=this.workingColorSpace){return r.fromArray(this.spaces[s].luminanceCoefficients)},define:function(r){Object.assign(this.spaces,r)},_getMatrix:function(r,s,a){return r.copy(this.spaces[s].toXYZ).multiply(this.spaces[a].fromXYZ)},_getDrawingBufferColorSpace:function(r){return this.spaces[r].outputColorSpaceConfig.drawingBufferColorSpace},_getUnpackColorSpace:function(r=this.workingColorSpace){return this.spaces[r].workingColorSpaceConfig.unpackColorSpace},fromWorkingColorSpace:function(r,s){return ur("THREE.ColorManagement: .fromWorkingColorSpace() has been renamed to .workingToColorSpace()."),i.workingToColorSpace(r,s)},toWorkingColorSpace:function(r,s){return ur("THREE.ColorManagement: .toWorkingColorSpace() has been renamed to .colorSpaceToWorking()."),i.colorSpaceToWorking(r,s)}},e=[.64,.33,.3,.6,.15,.06],t=[.2126,.7152,.0722],n=[.3127,.329];return i.define({[Ti]:{primaries:e,whitePoint:n,transfer:Hr,toXYZ:Gc,fromXYZ:Wc,luminanceCoefficients:t,workingColorSpaceConfig:{unpackColorSpace:Nt},outputColorSpaceConfig:{drawingBufferColorSpace:Nt}},[Nt]:{primaries:e,whitePoint:n,transfer:tt,toXYZ:Gc,fromXYZ:Wc,luminanceCoefficients:t,outputColorSpaceConfig:{drawingBufferColorSpace:Nt}}}),i}var Ke=Xh();function Vn(i){return i<.04045?i*.0773993808:Math.pow(i*.9478672986+.0521327014,2.4)}function lr(i){return i<.0031308?i*12.92:1.055*Math.pow(i,.41666)-.055}var Xi,ha=class{static getDataURL(e,t="image/png"){if(/^data:/i.test(e.src)||typeof HTMLCanvasElement>"u")return e.src;let n;if(e instanceof HTMLCanvasElement)n=e;else{Xi===void 0&&(Xi=Gr("canvas")),Xi.width=e.width,Xi.height=e.height;let r=Xi.getContext("2d");e instanceof ImageData?r.putImageData(e,0,0):r.drawImage(e,0,0,e.width,e.height),n=Xi}return n.toDataURL(t)}static sRGBToLinear(e){if(typeof HTMLImageElement<"u"&&e instanceof HTMLImageElement||typeof HTMLCanvasElement<"u"&&e instanceof HTMLCanvasElement||typeof ImageBitmap<"u"&&e instanceof ImageBitmap){let t=Gr("canvas");t.width=e.width,t.height=e.height;let n=t.getContext("2d");n.drawImage(e,0,0,e.width,e.height);let r=n.getImageData(0,0,e.width,e.height),s=r.data;for(let a=0;a<s.length;a++)s[a]=Vn(s[a]/255)*255;return n.putImageData(r,0,0),t}else if(e.data){let t=e.data.slice(0);for(let n=0;n<t.length;n++)t instanceof Uint8Array||t instanceof Uint8ClampedArray?t[n]=Math.floor(Vn(t[n]/255)*255):t[n]=Vn(t[n]);return{data:t,width:e.width,height:e.height}}else return console.warn("THREE.ImageUtils.sRGBToLinear(): Unsupported image type. No color space conversion applied."),e}},$h=0,hr=class{constructor(e=null){this.isSource=!0,Object.defineProperty(this,"id",{value:$h++}),this.uuid=Hn(),this.data=e,this.dataReady=!0,this.version=0}getSize(e){let t=this.data;return typeof HTMLVideoElement<"u"&&t instanceof HTMLVideoElement?e.set(t.videoWidth,t.videoHeight,0):t instanceof VideoFrame?e.set(t.displayHeight,t.displayWidth,0):t!==null?e.set(t.width,t.height,t.depth||0):e.set(0,0,0),e}set needsUpdate(e){e===!0&&this.version++}toJSON(e){let t=e===void 0||typeof e=="string";if(!t&&e.images[this.uuid]!==void 0)return e.images[this.uuid];let n={uuid:this.uuid,url:""},r=this.data;if(r!==null){let s;if(Array.isArray(r)){s=[];for(let a=0,o=r.length;a<o;a++)r[a].isDataTexture?s.push(Zo(r[a].image)):s.push(Zo(r[a]))}else s=Zo(r);n.url=s}return t||(e.images[this.uuid]=n),n}};function Zo(i){return typeof HTMLImageElement<"u"&&i instanceof HTMLImageElement||typeof HTMLCanvasElement<"u"&&i instanceof HTMLCanvasElement||typeof ImageBitmap<"u"&&i instanceof ImageBitmap?ha.getDataURL(i):i.data?{data:Array.from(i.data),width:i.width,height:i.height,type:i.data.constructor.name}:(console.warn("THREE.Texture: Unable to serialize Texture."),{})}var qh=0,Jo=new D,Lt=class i extends Wn{constructor(e=i.DEFAULT_IMAGE,t=i.DEFAULT_MAPPING,n=si,r=si,s=bn,a=fi,o=hn,c=Sn,l=i.DEFAULT_ANISOTROPY,u=Yn){super(),this.isTexture=!0,Object.defineProperty(this,"id",{value:qh++}),this.uuid=Hn(),this.name="",this.source=new hr(e),this.mipmaps=[],this.mapping=t,this.channel=0,this.wrapS=n,this.wrapT=r,this.magFilter=s,this.minFilter=a,this.anisotropy=l,this.format=o,this.internalFormat=null,this.type=c,this.offset=new We(0,0),this.repeat=new We(1,1),this.center=new We(0,0),this.rotation=0,this.matrixAutoUpdate=!0,this.matrix=new ke,this.generateMipmaps=!0,this.premultiplyAlpha=!1,this.flipY=!0,this.unpackAlignment=4,this.colorSpace=u,this.userData={},this.updateRanges=[],this.version=0,this.onUpdate=null,this.renderTarget=null,this.isRenderTargetTexture=!1,this.isArrayTexture=!!(e&&e.depth&&e.depth>1),this.pmremVersion=0}get width(){return this.source.getSize(Jo).x}get height(){return this.source.getSize(Jo).y}get depth(){return this.source.getSize(Jo).z}get image(){return this.source.data}set image(e=null){this.source.data=e}updateMatrix(){this.matrix.setUvTransform(this.offset.x,this.offset.y,this.repeat.x,this.repeat.y,this.rotation,this.center.x,this.center.y)}addUpdateRange(e,t){this.updateRanges.push({start:e,count:t})}clearUpdateRanges(){this.updateRanges.length=0}clone(){return new this.constructor().copy(this)}copy(e){return this.name=e.name,this.source=e.source,this.mipmaps=e.mipmaps.slice(0),this.mapping=e.mapping,this.channel=e.channel,this.wrapS=e.wrapS,this.wrapT=e.wrapT,this.magFilter=e.magFilter,this.minFilter=e.minFilter,this.anisotropy=e.anisotropy,this.format=e.format,this.internalFormat=e.internalFormat,this.type=e.type,this.offset.copy(e.offset),this.repeat.copy(e.repeat),this.center.copy(e.center),this.rotation=e.rotation,this.matrixAutoUpdate=e.matrixAutoUpdate,this.matrix.copy(e.matrix),this.generateMipmaps=e.generateMipmaps,this.premultiplyAlpha=e.premultiplyAlpha,this.flipY=e.flipY,this.unpackAlignment=e.unpackAlignment,this.colorSpace=e.colorSpace,this.renderTarget=e.renderTarget,this.isRenderTargetTexture=e.isRenderTargetTexture,this.isArrayTexture=e.isArrayTexture,this.userData=JSON.parse(JSON.stringify(e.userData)),this.needsUpdate=!0,this}setValues(e){for(let t in e){let n=e[t];if(n===void 0){console.warn(`THREE.Texture.setValues(): parameter '${t}' has value of undefined.`);continue}let r=this[t];if(r===void 0){console.warn(`THREE.Texture.setValues(): property '${t}' does not exist.`);continue}r&&n&&r.isVector2&&n.isVector2||r&&n&&r.isVector3&&n.isVector3||r&&n&&r.isMatrix3&&n.isMatrix3?r.copy(n):this[t]=n}}toJSON(e){let t=e===void 0||typeof e=="string";if(!t&&e.textures[this.uuid]!==void 0)return e.textures[this.uuid];let n={metadata:{version:4.7,type:"Texture",generator:"Texture.toJSON"},uuid:this.uuid,name:this.name,image:this.source.toJSON(e).uuid,mapping:this.mapping,channel:this.channel,repeat:[this.repeat.x,this.repeat.y],offset:[this.offset.x,this.offset.y],center:[this.center.x,this.center.y],rotation:this.rotation,wrap:[this.wrapS,this.wrapT],format:this.format,internalFormat:this.internalFormat,type:this.type,colorSpace:this.colorSpace,minFilter:this.minFilter,magFilter:this.magFilter,anisotropy:this.anisotropy,flipY:this.flipY,generateMipmaps:this.generateMipmaps,premultiplyAlpha:this.premultiplyAlpha,unpackAlignment:this.unpackAlignment};return Object.keys(this.userData).length>0&&(n.userData=this.userData),t||(e.textures[this.uuid]=n),n}dispose(){this.dispatchEvent({type:"dispose"})}transformUv(e){if(this.mapping!==Dl)return e;if(e.applyMatrix3(this.matrix),e.x<0||e.x>1)switch(this.wrapS){case la:e.x=e.x-Math.floor(e.x);break;case si:e.x=e.x<0?0:1;break;case ca:Math.abs(Math.floor(e.x)%2)===1?e.x=Math.ceil(e.x)-e.x:e.x=e.x-Math.floor(e.x);break}if(e.y<0||e.y>1)switch(this.wrapT){case la:e.y=e.y-Math.floor(e.y);break;case si:e.y=e.y<0?0:1;break;case ca:Math.abs(Math.floor(e.y)%2)===1?e.y=Math.ceil(e.y)-e.y:e.y=e.y-Math.floor(e.y);break}return this.flipY&&(e.y=1-e.y),e}set needsUpdate(e){e===!0&&(this.version++,this.source.needsUpdate=!0)}set needsPMREMUpdate(e){e===!0&&this.pmremVersion++}};Lt.DEFAULT_IMAGE=null;Lt.DEFAULT_MAPPING=Dl;Lt.DEFAULT_ANISOTROPY=1;var xt=class i{constructor(e=0,t=0,n=0,r=1){i.prototype.isVector4=!0,this.x=e,this.y=t,this.z=n,this.w=r}get width(){return this.z}set width(e){this.z=e}get height(){return this.w}set height(e){this.w=e}set(e,t,n,r){return this.x=e,this.y=t,this.z=n,this.w=r,this}setScalar(e){return this.x=e,this.y=e,this.z=e,this.w=e,this}setX(e){return this.x=e,this}setY(e){return this.y=e,this}setZ(e){return this.z=e,this}setW(e){return this.w=e,this}setComponent(e,t){switch(e){case 0:this.x=t;break;case 1:this.y=t;break;case 2:this.z=t;break;case 3:this.w=t;break;default:throw new Error("index is out of range: "+e)}return this}getComponent(e){switch(e){case 0:return this.x;case 1:return this.y;case 2:return this.z;case 3:return this.w;default:throw new Error("index is out of range: "+e)}}clone(){return new this.constructor(this.x,this.y,this.z,this.w)}copy(e){return this.x=e.x,this.y=e.y,this.z=e.z,this.w=e.w!==void 0?e.w:1,this}add(e){return this.x+=e.x,this.y+=e.y,this.z+=e.z,this.w+=e.w,this}addScalar(e){return this.x+=e,this.y+=e,this.z+=e,this.w+=e,this}addVectors(e,t){return this.x=e.x+t.x,this.y=e.y+t.y,this.z=e.z+t.z,this.w=e.w+t.w,this}addScaledVector(e,t){return this.x+=e.x*t,this.y+=e.y*t,this.z+=e.z*t,this.w+=e.w*t,this}sub(e){return this.x-=e.x,this.y-=e.y,this.z-=e.z,this.w-=e.w,this}subScalar(e){return this.x-=e,this.y-=e,this.z-=e,this.w-=e,this}subVectors(e,t){return this.x=e.x-t.x,this.y=e.y-t.y,this.z=e.z-t.z,this.w=e.w-t.w,this}multiply(e){return this.x*=e.x,this.y*=e.y,this.z*=e.z,this.w*=e.w,this}multiplyScalar(e){return this.x*=e,this.y*=e,this.z*=e,this.w*=e,this}applyMatrix4(e){let t=this.x,n=this.y,r=this.z,s=this.w,a=e.elements;return this.x=a[0]*t+a[4]*n+a[8]*r+a[12]*s,this.y=a[1]*t+a[5]*n+a[9]*r+a[13]*s,this.z=a[2]*t+a[6]*n+a[10]*r+a[14]*s,this.w=a[3]*t+a[7]*n+a[11]*r+a[15]*s,this}divide(e){return this.x/=e.x,this.y/=e.y,this.z/=e.z,this.w/=e.w,this}divideScalar(e){return this.multiplyScalar(1/e)}setAxisAngleFromQuaternion(e){this.w=2*Math.acos(e.w);let t=Math.sqrt(1-e.w*e.w);return t<1e-4?(this.x=1,this.y=0,this.z=0):(this.x=e.x/t,this.y=e.y/t,this.z=e.z/t),this}setAxisAngleFromRotationMatrix(e){let t,n,r,s,c=e.elements,l=c[0],u=c[4],d=c[8],h=c[1],p=c[5],g=c[9],x=c[2],m=c[6],f=c[10];if(Math.abs(u-h)<.01&&Math.abs(d-x)<.01&&Math.abs(g-m)<.01){if(Math.abs(u+h)<.1&&Math.abs(d+x)<.1&&Math.abs(g+m)<.1&&Math.abs(l+p+f-3)<.1)return this.set(1,0,0,0),this;t=Math.PI;let M=(l+1)/2,y=(p+1)/2,C=(f+1)/2,A=(u+h)/4,I=(d+x)/4,N=(g+m)/4;return M>y&&M>C?M<.01?(n=0,r=.707106781,s=.707106781):(n=Math.sqrt(M),r=A/n,s=I/n):y>C?y<.01?(n=.707106781,r=0,s=.707106781):(r=Math.sqrt(y),n=A/r,s=N/r):C<.01?(n=.707106781,r=.707106781,s=0):(s=Math.sqrt(C),n=I/s,r=N/s),this.set(n,r,s,t),this}let S=Math.sqrt((m-g)*(m-g)+(d-x)*(d-x)+(h-u)*(h-u));return Math.abs(S)<.001&&(S=1),this.x=(m-g)/S,this.y=(d-x)/S,this.z=(h-u)/S,this.w=Math.acos((l+p+f-1)/2),this}setFromMatrixPosition(e){let t=e.elements;return this.x=t[12],this.y=t[13],this.z=t[14],this.w=t[15],this}min(e){return this.x=Math.min(this.x,e.x),this.y=Math.min(this.y,e.y),this.z=Math.min(this.z,e.z),this.w=Math.min(this.w,e.w),this}max(e){return this.x=Math.max(this.x,e.x),this.y=Math.max(this.y,e.y),this.z=Math.max(this.z,e.z),this.w=Math.max(this.w,e.w),this}clamp(e,t){return this.x=Ye(this.x,e.x,t.x),this.y=Ye(this.y,e.y,t.y),this.z=Ye(this.z,e.z,t.z),this.w=Ye(this.w,e.w,t.w),this}clampScalar(e,t){return this.x=Ye(this.x,e,t),this.y=Ye(this.y,e,t),this.z=Ye(this.z,e,t),this.w=Ye(this.w,e,t),this}clampLength(e,t){let n=this.length();return this.divideScalar(n||1).multiplyScalar(Ye(n,e,t))}floor(){return this.x=Math.floor(this.x),this.y=Math.floor(this.y),this.z=Math.floor(this.z),this.w=Math.floor(this.w),this}ceil(){return this.x=Math.ceil(this.x),this.y=Math.ceil(this.y),this.z=Math.ceil(this.z),this.w=Math.ceil(this.w),this}round(){return this.x=Math.round(this.x),this.y=Math.round(this.y),this.z=Math.round(this.z),this.w=Math.round(this.w),this}roundToZero(){return this.x=Math.trunc(this.x),this.y=Math.trunc(this.y),this.z=Math.trunc(this.z),this.w=Math.trunc(this.w),this}negate(){return this.x=-this.x,this.y=-this.y,this.z=-this.z,this.w=-this.w,this}dot(e){return this.x*e.x+this.y*e.y+this.z*e.z+this.w*e.w}lengthSq(){return this.x*this.x+this.y*this.y+this.z*this.z+this.w*this.w}length(){return Math.sqrt(this.x*this.x+this.y*this.y+this.z*this.z+this.w*this.w)}manhattanLength(){return Math.abs(this.x)+Math.abs(this.y)+Math.abs(this.z)+Math.abs(this.w)}normalize(){return this.divideScalar(this.length()||1)}setLength(e){return this.normalize().multiplyScalar(e)}lerp(e,t){return this.x+=(e.x-this.x)*t,this.y+=(e.y-this.y)*t,this.z+=(e.z-this.z)*t,this.w+=(e.w-this.w)*t,this}lerpVectors(e,t,n){return this.x=e.x+(t.x-e.x)*n,this.y=e.y+(t.y-e.y)*n,this.z=e.z+(t.z-e.z)*n,this.w=e.w+(t.w-e.w)*n,this}equals(e){return e.x===this.x&&e.y===this.y&&e.z===this.z&&e.w===this.w}fromArray(e,t=0){return this.x=e[t],this.y=e[t+1],this.z=e[t+2],this.w=e[t+3],this}toArray(e=[],t=0){return e[t]=this.x,e[t+1]=this.y,e[t+2]=this.z,e[t+3]=this.w,e}fromBufferAttribute(e,t){return this.x=e.getX(t),this.y=e.getY(t),this.z=e.getZ(t),this.w=e.getW(t),this}random(){return this.x=Math.random(),this.y=Math.random(),this.z=Math.random(),this.w=Math.random(),this}*[Symbol.iterator](){yield this.x,yield this.y,yield this.z,yield this.w}},fa=class extends Wn{constructor(e=1,t=1,n={}){super(),n=Object.assign({generateMipmaps:!1,internalFormat:null,minFilter:bn,depthBuffer:!0,stencilBuffer:!1,resolveDepthBuffer:!0,resolveStencilBuffer:!0,depthTexture:null,samples:0,count:1,depth:1,multiview:!1},n),this.isRenderTarget=!0,this.width=e,this.height=t,this.depth=n.depth,this.scissor=new xt(0,0,e,t),this.scissorTest=!1,this.viewport=new xt(0,0,e,t);let r={width:e,height:t,depth:n.depth},s=new Lt(r);this.textures=[];let a=n.count;for(let o=0;o<a;o++)this.textures[o]=s.clone(),this.textures[o].isRenderTargetTexture=!0,this.textures[o].renderTarget=this;this._setTextureOptions(n),this.depthBuffer=n.depthBuffer,this.stencilBuffer=n.stencilBuffer,this.resolveDepthBuffer=n.resolveDepthBuffer,this.resolveStencilBuffer=n.resolveStencilBuffer,this._depthTexture=null,this.depthTexture=n.depthTexture,this.samples=n.samples,this.multiview=n.multiview}_setTextureOptions(e={}){let t={minFilter:bn,generateMipmaps:!1,flipY:!1,internalFormat:null};e.mapping!==void 0&&(t.mapping=e.mapping),e.wrapS!==void 0&&(t.wrapS=e.wrapS),e.wrapT!==void 0&&(t.wrapT=e.wrapT),e.wrapR!==void 0&&(t.wrapR=e.wrapR),e.magFilter!==void 0&&(t.magFilter=e.magFilter),e.minFilter!==void 0&&(t.minFilter=e.minFilter),e.format!==void 0&&(t.format=e.format),e.type!==void 0&&(t.type=e.type),e.anisotropy!==void 0&&(t.anisotropy=e.anisotropy),e.colorSpace!==void 0&&(t.colorSpace=e.colorSpace),e.flipY!==void 0&&(t.flipY=e.flipY),e.generateMipmaps!==void 0&&(t.generateMipmaps=e.generateMipmaps),e.internalFormat!==void 0&&(t.internalFormat=e.internalFormat);for(let n=0;n<this.textures.length;n++)this.textures[n].setValues(t)}get texture(){return this.textures[0]}set texture(e){this.textures[0]=e}set depthTexture(e){this._depthTexture!==null&&(this._depthTexture.renderTarget=null),e!==null&&(e.renderTarget=this),this._depthTexture=e}get depthTexture(){return this._depthTexture}setSize(e,t,n=1){if(this.width!==e||this.height!==t||this.depth!==n){this.width=e,this.height=t,this.depth=n;for(let r=0,s=this.textures.length;r<s;r++)this.textures[r].image.width=e,this.textures[r].image.height=t,this.textures[r].image.depth=n,this.textures[r].isArrayTexture=this.textures[r].image.depth>1;this.dispose()}this.viewport.set(0,0,e,t),this.scissor.set(0,0,e,t)}clone(){return new this.constructor().copy(this)}copy(e){this.width=e.width,this.height=e.height,this.depth=e.depth,this.scissor.copy(e.scissor),this.scissorTest=e.scissorTest,this.viewport.copy(e.viewport),this.textures.length=0;for(let t=0,n=e.textures.length;t<n;t++){this.textures[t]=e.textures[t].clone(),this.textures[t].isRenderTargetTexture=!0,this.textures[t].renderTarget=this;let r=Object.assign({},e.textures[t].image);this.textures[t].source=new hr(r)}return this.depthBuffer=e.depthBuffer,this.stencilBuffer=e.stencilBuffer,this.resolveDepthBuffer=e.resolveDepthBuffer,this.resolveStencilBuffer=e.resolveStencilBuffer,e.depthTexture!==null&&(this.depthTexture=e.depthTexture.clone()),this.samples=e.samples,this}dispose(){this.dispatchEvent({type:"dispose"})}},Rn=class extends fa{constructor(e=1,t=1,n={}){super(e,t,n),this.isWebGLRenderTarget=!0}},Wr=class extends Lt{constructor(e=null,t=1,n=1,r=1){super(null),this.isDataArrayTexture=!0,this.image={data:e,width:t,height:n,depth:r},this.magFilter=dn,this.minFilter=dn,this.wrapR=si,this.generateMipmaps=!1,this.flipY=!1,this.unpackAlignment=1,this.layerUpdates=new Set}addLayerUpdate(e){this.layerUpdates.add(e)}clearLayerUpdates(){this.layerUpdates.clear()}};var pa=class extends Lt{constructor(e=null,t=1,n=1,r=1){super(null),this.isData3DTexture=!0,this.image={data:e,width:t,height:n,depth:r},this.magFilter=dn,this.minFilter=dn,this.wrapR=si,this.generateMipmaps=!1,this.flipY=!1,this.unpackAlignment=1}};var oi=class{constructor(e=new D(1/0,1/0,1/0),t=new D(-1/0,-1/0,-1/0)){this.isBox3=!0,this.min=e,this.max=t}set(e,t){return this.min.copy(e),this.max.copy(t),this}setFromArray(e){this.makeEmpty();for(let t=0,n=e.length;t<n;t+=3)this.expandByPoint(gn.fromArray(e,t));return this}setFromBufferAttribute(e){this.makeEmpty();for(let t=0,n=e.count;t<n;t++)this.expandByPoint(gn.fromBufferAttribute(e,t));return this}setFromPoints(e){this.makeEmpty();for(let t=0,n=e.length;t<n;t++)this.expandByPoint(e[t]);return this}setFromCenterAndSize(e,t){let n=gn.copy(t).multiplyScalar(.5);return this.min.copy(e).sub(n),this.max.copy(e).add(n),this}setFromObject(e,t=!1){return this.makeEmpty(),this.expandByObject(e,t)}clone(){return new this.constructor().copy(this)}copy(e){return this.min.copy(e.min),this.max.copy(e.max),this}makeEmpty(){return this.min.x=this.min.y=this.min.z=1/0,this.max.x=this.max.y=this.max.z=-1/0,this}isEmpty(){return this.max.x<this.min.x||this.max.y<this.min.y||this.max.z<this.min.z}getCenter(e){return this.isEmpty()?e.set(0,0,0):e.addVectors(this.min,this.max).multiplyScalar(.5)}getSize(e){return this.isEmpty()?e.set(0,0,0):e.subVectors(this.max,this.min)}expandByPoint(e){return this.min.min(e),this.max.max(e),this}expandByVector(e){return this.min.sub(e),this.max.add(e),this}expandByScalar(e){return this.min.addScalar(-e),this.max.addScalar(e),this}expandByObject(e,t=!1){e.updateWorldMatrix(!1,!1);let n=e.geometry;if(n!==void 0){let s=n.getAttribute("position");if(t===!0&&s!==void 0&&e.isInstancedMesh!==!0)for(let a=0,o=s.count;a<o;a++)e.isMesh===!0?e.getVertexPosition(a,gn):gn.fromBufferAttribute(s,a),gn.applyMatrix4(e.matrixWorld),this.expandByPoint(gn);else e.boundingBox!==void 0?(e.boundingBox===null&&e.computeBoundingBox(),Is.copy(e.boundingBox)):(n.boundingBox===null&&n.computeBoundingBox(),Is.copy(n.boundingBox)),Is.applyMatrix4(e.matrixWorld),this.union(Is)}let r=e.children;for(let s=0,a=r.length;s<a;s++)this.expandByObject(r[s],t);return this}containsPoint(e){return e.x>=this.min.x&&e.x<=this.max.x&&e.y>=this.min.y&&e.y<=this.max.y&&e.z>=this.min.z&&e.z<=this.max.z}containsBox(e){return this.min.x<=e.min.x&&e.max.x<=this.max.x&&this.min.y<=e.min.y&&e.max.y<=this.max.y&&this.min.z<=e.min.z&&e.max.z<=this.max.z}getParameter(e,t){return t.set((e.x-this.min.x)/(this.max.x-this.min.x),(e.y-this.min.y)/(this.max.y-this.min.y),(e.z-this.min.z)/(this.max.z-this.min.z))}intersectsBox(e){return e.max.x>=this.min.x&&e.min.x<=this.max.x&&e.max.y>=this.min.y&&e.min.y<=this.max.y&&e.max.z>=this.min.z&&e.min.z<=this.max.z}intersectsSphere(e){return this.clampPoint(e.center,gn),gn.distanceToSquared(e.center)<=e.radius*e.radius}intersectsPlane(e){let t,n;return e.normal.x>0?(t=e.normal.x*this.min.x,n=e.normal.x*this.max.x):(t=e.normal.x*this.max.x,n=e.normal.x*this.min.x),e.normal.y>0?(t+=e.normal.y*this.min.y,n+=e.normal.y*this.max.y):(t+=e.normal.y*this.max.y,n+=e.normal.y*this.min.y),e.normal.z>0?(t+=e.normal.z*this.min.z,n+=e.normal.z*this.max.z):(t+=e.normal.z*this.max.z,n+=e.normal.z*this.min.z),t<=-e.constant&&n>=-e.constant}intersectsTriangle(e){if(this.isEmpty())return!1;this.getCenter(Pr),Ps.subVectors(this.max,Pr),$i.subVectors(e.a,Pr),qi.subVectors(e.b,Pr),Yi.subVectors(e.c,Pr),Qn.subVectors(qi,$i),ei.subVectors(Yi,qi),yi.subVectors($i,Yi);let t=[0,-Qn.z,Qn.y,0,-ei.z,ei.y,0,-yi.z,yi.y,Qn.z,0,-Qn.x,ei.z,0,-ei.x,yi.z,0,-yi.x,-Qn.y,Qn.x,0,-ei.y,ei.x,0,-yi.y,yi.x,0];return!Ko(t,$i,qi,Yi,Ps)||(t=[1,0,0,0,1,0,0,0,1],!Ko(t,$i,qi,Yi,Ps))?!1:(Ns.crossVectors(Qn,ei),t=[Ns.x,Ns.y,Ns.z],Ko(t,$i,qi,Yi,Ps))}clampPoint(e,t){return t.copy(e).clamp(this.min,this.max)}distanceToPoint(e){return this.clampPoint(e,gn).distanceTo(e)}getBoundingSphere(e){return this.isEmpty()?e.makeEmpty():(this.getCenter(e.center),e.radius=this.getSize(gn).length()*.5),e}intersect(e){return this.min.max(e.min),this.max.min(e.max),this.isEmpty()&&this.makeEmpty(),this}union(e){return this.min.min(e.min),this.max.max(e.max),this}applyMatrix4(e){return this.isEmpty()?this:(Un[0].set(this.min.x,this.min.y,this.min.z).applyMatrix4(e),Un[1].set(this.min.x,this.min.y,this.max.z).applyMatrix4(e),Un[2].set(this.min.x,this.max.y,this.min.z).applyMatrix4(e),Un[3].set(this.min.x,this.max.y,this.max.z).applyMatrix4(e),Un[4].set(this.max.x,this.min.y,this.min.z).applyMatrix4(e),Un[5].set(this.max.x,this.min.y,this.max.z).applyMatrix4(e),Un[6].set(this.max.x,this.max.y,this.min.z).applyMatrix4(e),Un[7].set(this.max.x,this.max.y,this.max.z).applyMatrix4(e),this.setFromPoints(Un),this)}translate(e){return this.min.add(e),this.max.add(e),this}equals(e){return e.min.equals(this.min)&&e.max.equals(this.max)}toJSON(){return{min:this.min.toArray(),max:this.max.toArray()}}fromJSON(e){return this.min.fromArray(e.min),this.max.fromArray(e.max),this}},Un=[new D,new D,new D,new D,new D,new D,new D,new D],gn=new D,Is=new oi,$i=new D,qi=new D,Yi=new D,Qn=new D,ei=new D,yi=new D,Pr=new D,Ps=new D,Ns=new D,vi=new D;function Ko(i,e,t,n,r){for(let s=0,a=i.length-3;s<=a;s+=3){vi.fromArray(i,s);let o=r.x*Math.abs(vi.x)+r.y*Math.abs(vi.y)+r.z*Math.abs(vi.z),c=e.dot(vi),l=t.dot(vi),u=n.dot(vi);if(Math.max(-Math.max(c,l,u),Math.min(c,l,u))>o)return!1}return!0}var Yh=new oi,Nr=new D,jo=new D,li=class{constructor(e=new D,t=-1){this.isSphere=!0,this.center=e,this.radius=t}set(e,t){return this.center.copy(e),this.radius=t,this}setFromPoints(e,t){let n=this.center;t!==void 0?n.copy(t):Yh.setFromPoints(e).getCenter(n);let r=0;for(let s=0,a=e.length;s<a;s++)r=Math.max(r,n.distanceToSquared(e[s]));return this.radius=Math.sqrt(r),this}copy(e){return this.center.copy(e.center),this.radius=e.radius,this}isEmpty(){return this.radius<0}makeEmpty(){return this.center.set(0,0,0),this.radius=-1,this}containsPoint(e){return e.distanceToSquared(this.center)<=this.radius*this.radius}distanceToPoint(e){return e.distanceTo(this.center)-this.radius}intersectsSphere(e){let t=this.radius+e.radius;return e.center.distanceToSquared(this.center)<=t*t}intersectsBox(e){return e.intersectsSphere(this)}intersectsPlane(e){return Math.abs(e.distanceToPoint(this.center))<=this.radius}clampPoint(e,t){let n=this.center.distanceToSquared(e);return t.copy(e),n>this.radius*this.radius&&(t.sub(this.center).normalize(),t.multiplyScalar(this.radius).add(this.center)),t}getBoundingBox(e){return this.isEmpty()?(e.makeEmpty(),e):(e.set(this.center,this.center),e.expandByScalar(this.radius),e)}applyMatrix4(e){return this.center.applyMatrix4(e),this.radius=this.radius*e.getMaxScaleOnAxis(),this}translate(e){return this.center.add(e),this}expandByPoint(e){if(this.isEmpty())return this.center.copy(e),this.radius=0,this;Nr.subVectors(e,this.center);let t=Nr.lengthSq();if(t>this.radius*this.radius){let n=Math.sqrt(t),r=(n-this.radius)*.5;this.center.addScaledVector(Nr,r/n),this.radius+=r}return this}union(e){return e.isEmpty()?this:this.isEmpty()?(this.copy(e),this):(this.center.equals(e.center)===!0?this.radius=Math.max(this.radius,e.radius):(jo.subVectors(e.center,this.center).setLength(e.radius),this.expandByPoint(Nr.copy(e.center).add(jo)),this.expandByPoint(Nr.copy(e.center).sub(jo))),this)}equals(e){return e.center.equals(this.center)&&e.radius===this.radius}clone(){return new this.constructor().copy(this)}toJSON(){return{radius:this.radius,center:this.center.toArray()}}fromJSON(e){return this.radius=e.radius,this.center.fromArray(e.center),this}},On=new D,Qo=new D,Ds=new D,ti=new D,el=new D,Ls=new D,tl=new D,fr=class{constructor(e=new D,t=new D(0,0,-1)){this.origin=e,this.direction=t}set(e,t){return this.origin.copy(e),this.direction.copy(t),this}copy(e){return this.origin.copy(e.origin),this.direction.copy(e.direction),this}at(e,t){return t.copy(this.origin).addScaledVector(this.direction,e)}lookAt(e){return this.direction.copy(e).sub(this.origin).normalize(),this}recast(e){return this.origin.copy(this.at(e,On)),this}closestPointToPoint(e,t){t.subVectors(e,this.origin);let n=t.dot(this.direction);return n<0?t.copy(this.origin):t.copy(this.origin).addScaledVector(this.direction,n)}distanceToPoint(e){return Math.sqrt(this.distanceSqToPoint(e))}distanceSqToPoint(e){let t=On.subVectors(e,this.origin).dot(this.direction);return t<0?this.origin.distanceToSquared(e):(On.copy(this.origin).addScaledVector(this.direction,t),On.distanceToSquared(e))}distanceSqToSegment(e,t,n,r){Qo.copy(e).add(t).multiplyScalar(.5),Ds.copy(t).sub(e).normalize(),ti.copy(this.origin).sub(Qo);let s=e.distanceTo(t)*.5,a=-this.direction.dot(Ds),o=ti.dot(this.direction),c=-ti.dot(Ds),l=ti.lengthSq(),u=Math.abs(1-a*a),d,h,p,g;if(u>0)if(d=a*c-o,h=a*o-c,g=s*u,d>=0)if(h>=-g)if(h<=g){let x=1/u;d*=x,h*=x,p=d*(d+a*h+2*o)+h*(a*d+h+2*c)+l}else h=s,d=Math.max(0,-(a*h+o)),p=-d*d+h*(h+2*c)+l;else h=-s,d=Math.max(0,-(a*h+o)),p=-d*d+h*(h+2*c)+l;else h<=-g?(d=Math.max(0,-(-a*s+o)),h=d>0?-s:Math.min(Math.max(-s,-c),s),p=-d*d+h*(h+2*c)+l):h<=g?(d=0,h=Math.min(Math.max(-s,-c),s),p=h*(h+2*c)+l):(d=Math.max(0,-(a*s+o)),h=d>0?s:Math.min(Math.max(-s,-c),s),p=-d*d+h*(h+2*c)+l);else h=a>0?-s:s,d=Math.max(0,-(a*h+o)),p=-d*d+h*(h+2*c)+l;return n&&n.copy(this.origin).addScaledVector(this.direction,d),r&&r.copy(Qo).addScaledVector(Ds,h),p}intersectSphere(e,t){On.subVectors(e.center,this.origin);let n=On.dot(this.direction),r=On.dot(On)-n*n,s=e.radius*e.radius;if(r>s)return null;let a=Math.sqrt(s-r),o=n-a,c=n+a;return c<0?null:o<0?this.at(c,t):this.at(o,t)}intersectsSphere(e){return e.radius<0?!1:this.distanceSqToPoint(e.center)<=e.radius*e.radius}distanceToPlane(e){let t=e.normal.dot(this.direction);if(t===0)return e.distanceToPoint(this.origin)===0?0:null;let n=-(this.origin.dot(e.normal)+e.constant)/t;return n>=0?n:null}intersectPlane(e,t){let n=this.distanceToPlane(e);return n===null?null:this.at(n,t)}intersectsPlane(e){let t=e.distanceToPoint(this.origin);return t===0||e.normal.dot(this.direction)*t<0}intersectBox(e,t){let n,r,s,a,o,c,l=1/this.direction.x,u=1/this.direction.y,d=1/this.direction.z,h=this.origin;return l>=0?(n=(e.min.x-h.x)*l,r=(e.max.x-h.x)*l):(n=(e.max.x-h.x)*l,r=(e.min.x-h.x)*l),u>=0?(s=(e.min.y-h.y)*u,a=(e.max.y-h.y)*u):(s=(e.max.y-h.y)*u,a=(e.min.y-h.y)*u),n>a||s>r||((s>n||isNaN(n))&&(n=s),(a<r||isNaN(r))&&(r=a),d>=0?(o=(e.min.z-h.z)*d,c=(e.max.z-h.z)*d):(o=(e.max.z-h.z)*d,c=(e.min.z-h.z)*d),n>c||o>r)||((o>n||n!==n)&&(n=o),(c<r||r!==r)&&(r=c),r<0)?null:this.at(n>=0?n:r,t)}intersectsBox(e){return this.intersectBox(e,On)!==null}intersectTriangle(e,t,n,r,s){el.subVectors(t,e),Ls.subVectors(n,e),tl.crossVectors(el,Ls);let a=this.direction.dot(tl),o;if(a>0){if(r)return null;o=1}else if(a<0)o=-1,a=-a;else return null;ti.subVectors(this.origin,e);let c=o*this.direction.dot(Ls.crossVectors(ti,Ls));if(c<0)return null;let l=o*this.direction.dot(el.cross(ti));if(l<0||c+l>a)return null;let u=-o*ti.dot(tl);return u<0?null:this.at(u/a,s)}applyMatrix4(e){return this.origin.applyMatrix4(e),this.direction.transformDirection(e),this}equals(e){return e.origin.equals(this.origin)&&e.direction.equals(this.direction)}clone(){return new this.constructor().copy(this)}},ht=class i{constructor(e,t,n,r,s,a,o,c,l,u,d,h,p,g,x,m){i.prototype.isMatrix4=!0,this.elements=[1,0,0,0,0,1,0,0,0,0,1,0,0,0,0,1],e!==void 0&&this.set(e,t,n,r,s,a,o,c,l,u,d,h,p,g,x,m)}set(e,t,n,r,s,a,o,c,l,u,d,h,p,g,x,m){let f=this.elements;return f[0]=e,f[4]=t,f[8]=n,f[12]=r,f[1]=s,f[5]=a,f[9]=o,f[13]=c,f[2]=l,f[6]=u,f[10]=d,f[14]=h,f[3]=p,f[7]=g,f[11]=x,f[15]=m,this}identity(){return this.set(1,0,0,0,0,1,0,0,0,0,1,0,0,0,0,1),this}clone(){return new i().fromArray(this.elements)}copy(e){let t=this.elements,n=e.elements;return t[0]=n[0],t[1]=n[1],t[2]=n[2],t[3]=n[3],t[4]=n[4],t[5]=n[5],t[6]=n[6],t[7]=n[7],t[8]=n[8],t[9]=n[9],t[10]=n[10],t[11]=n[11],t[12]=n[12],t[13]=n[13],t[14]=n[14],t[15]=n[15],this}copyPosition(e){let t=this.elements,n=e.elements;return t[12]=n[12],t[13]=n[13],t[14]=n[14],this}setFromMatrix3(e){let t=e.elements;return this.set(t[0],t[3],t[6],0,t[1],t[4],t[7],0,t[2],t[5],t[8],0,0,0,0,1),this}extractBasis(e,t,n){return e.setFromMatrixColumn(this,0),t.setFromMatrixColumn(this,1),n.setFromMatrixColumn(this,2),this}makeBasis(e,t,n){return this.set(e.x,t.x,n.x,0,e.y,t.y,n.y,0,e.z,t.z,n.z,0,0,0,0,1),this}extractRotation(e){let t=this.elements,n=e.elements,r=1/Zi.setFromMatrixColumn(e,0).length(),s=1/Zi.setFromMatrixColumn(e,1).length(),a=1/Zi.setFromMatrixColumn(e,2).length();return t[0]=n[0]*r,t[1]=n[1]*r,t[2]=n[2]*r,t[3]=0,t[4]=n[4]*s,t[5]=n[5]*s,t[6]=n[6]*s,t[7]=0,t[8]=n[8]*a,t[9]=n[9]*a,t[10]=n[10]*a,t[11]=0,t[12]=0,t[13]=0,t[14]=0,t[15]=1,this}makeRotationFromEuler(e){let t=this.elements,n=e.x,r=e.y,s=e.z,a=Math.cos(n),o=Math.sin(n),c=Math.cos(r),l=Math.sin(r),u=Math.cos(s),d=Math.sin(s);if(e.order==="XYZ"){let h=a*u,p=a*d,g=o*u,x=o*d;t[0]=c*u,t[4]=-c*d,t[8]=l,t[1]=p+g*l,t[5]=h-x*l,t[9]=-o*c,t[2]=x-h*l,t[6]=g+p*l,t[10]=a*c}else if(e.order==="YXZ"){let h=c*u,p=c*d,g=l*u,x=l*d;t[0]=h+x*o,t[4]=g*o-p,t[8]=a*l,t[1]=a*d,t[5]=a*u,t[9]=-o,t[2]=p*o-g,t[6]=x+h*o,t[10]=a*c}else if(e.order==="ZXY"){let h=c*u,p=c*d,g=l*u,x=l*d;t[0]=h-x*o,t[4]=-a*d,t[8]=g+p*o,t[1]=p+g*o,t[5]=a*u,t[9]=x-h*o,t[2]=-a*l,t[6]=o,t[10]=a*c}else if(e.order==="ZYX"){let h=a*u,p=a*d,g=o*u,x=o*d;t[0]=c*u,t[4]=g*l-p,t[8]=h*l+x,t[1]=c*d,t[5]=x*l+h,t[9]=p*l-g,t[2]=-l,t[6]=o*c,t[10]=a*c}else if(e.order==="YZX"){let h=a*c,p=a*l,g=o*c,x=o*l;t[0]=c*u,t[4]=x-h*d,t[8]=g*d+p,t[1]=d,t[5]=a*u,t[9]=-o*u,t[2]=-l*u,t[6]=p*d+g,t[10]=h-x*d}else if(e.order==="XZY"){let h=a*c,p=a*l,g=o*c,x=o*l;t[0]=c*u,t[4]=-d,t[8]=l*u,t[1]=h*d+x,t[5]=a*u,t[9]=p*d-g,t[2]=g*d-p,t[6]=o*u,t[10]=x*d+h}return t[3]=0,t[7]=0,t[11]=0,t[12]=0,t[13]=0,t[14]=0,t[15]=1,this}makeRotationFromQuaternion(e){return this.compose(Zh,e,Jh)}lookAt(e,t,n){let r=this.elements;return jt.subVectors(e,t),jt.lengthSq()===0&&(jt.z=1),jt.normalize(),ni.crossVectors(n,jt),ni.lengthSq()===0&&(Math.abs(n.z)===1?jt.x+=1e-4:jt.z+=1e-4,jt.normalize(),ni.crossVectors(n,jt)),ni.normalize(),Fs.crossVectors(jt,ni),r[0]=ni.x,r[4]=Fs.x,r[8]=jt.x,r[1]=ni.y,r[5]=Fs.y,r[9]=jt.y,r[2]=ni.z,r[6]=Fs.z,r[10]=jt.z,this}multiply(e){return this.multiplyMatrices(this,e)}premultiply(e){return this.multiplyMatrices(e,this)}multiplyMatrices(e,t){let n=e.elements,r=t.elements,s=this.elements,a=n[0],o=n[4],c=n[8],l=n[12],u=n[1],d=n[5],h=n[9],p=n[13],g=n[2],x=n[6],m=n[10],f=n[14],S=n[3],M=n[7],y=n[11],C=n[15],A=r[0],I=r[4],N=r[8],v=r[12],b=r[1],T=r[5],P=r[9],U=r[13],F=r[2],k=r[6],G=r[10],K=r[14],W=r[3],se=r[7],de=r[11],Ae=r[15];return s[0]=a*A+o*b+c*F+l*W,s[4]=a*I+o*T+c*k+l*se,s[8]=a*N+o*P+c*G+l*de,s[12]=a*v+o*U+c*K+l*Ae,s[1]=u*A+d*b+h*F+p*W,s[5]=u*I+d*T+h*k+p*se,s[9]=u*N+d*P+h*G+p*de,s[13]=u*v+d*U+h*K+p*Ae,s[2]=g*A+x*b+m*F+f*W,s[6]=g*I+x*T+m*k+f*se,s[10]=g*N+x*P+m*G+f*de,s[14]=g*v+x*U+m*K+f*Ae,s[3]=S*A+M*b+y*F+C*W,s[7]=S*I+M*T+y*k+C*se,s[11]=S*N+M*P+y*G+C*de,s[15]=S*v+M*U+y*K+C*Ae,this}multiplyScalar(e){let t=this.elements;return t[0]*=e,t[4]*=e,t[8]*=e,t[12]*=e,t[1]*=e,t[5]*=e,t[9]*=e,t[13]*=e,t[2]*=e,t[6]*=e,t[10]*=e,t[14]*=e,t[3]*=e,t[7]*=e,t[11]*=e,t[15]*=e,this}determinant(){let e=this.elements,t=e[0],n=e[4],r=e[8],s=e[12],a=e[1],o=e[5],c=e[9],l=e[13],u=e[2],d=e[6],h=e[10],p=e[14],g=e[3],x=e[7],m=e[11],f=e[15];return g*(+s*c*d-r*l*d-s*o*h+n*l*h+r*o*p-n*c*p)+x*(+t*c*p-t*l*h+s*a*h-r*a*p+r*l*u-s*c*u)+m*(+t*l*d-t*o*p-s*a*d+n*a*p+s*o*u-n*l*u)+f*(-r*o*u-t*c*d+t*o*h+r*a*d-n*a*h+n*c*u)}transpose(){let e=this.elements,t;return t=e[1],e[1]=e[4],e[4]=t,t=e[2],e[2]=e[8],e[8]=t,t=e[6],e[6]=e[9],e[9]=t,t=e[3],e[3]=e[12],e[12]=t,t=e[7],e[7]=e[13],e[13]=t,t=e[11],e[11]=e[14],e[14]=t,this}setPosition(e,t,n){let r=this.elements;return e.isVector3?(r[12]=e.x,r[13]=e.y,r[14]=e.z):(r[12]=e,r[13]=t,r[14]=n),this}invert(){let e=this.elements,t=e[0],n=e[1],r=e[2],s=e[3],a=e[4],o=e[5],c=e[6],l=e[7],u=e[8],d=e[9],h=e[10],p=e[11],g=e[12],x=e[13],m=e[14],f=e[15],S=d*m*l-x*h*l+x*c*p-o*m*p-d*c*f+o*h*f,M=g*h*l-u*m*l-g*c*p+a*m*p+u*c*f-a*h*f,y=u*x*l-g*d*l+g*o*p-a*x*p-u*o*f+a*d*f,C=g*d*c-u*x*c-g*o*h+a*x*h+u*o*m-a*d*m,A=t*S+n*M+r*y+s*C;if(A===0)return this.set(0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0);let I=1/A;return e[0]=S*I,e[1]=(x*h*s-d*m*s-x*r*p+n*m*p+d*r*f-n*h*f)*I,e[2]=(o*m*s-x*c*s+x*r*l-n*m*l-o*r*f+n*c*f)*I,e[3]=(d*c*s-o*h*s-d*r*l+n*h*l+o*r*p-n*c*p)*I,e[4]=M*I,e[5]=(u*m*s-g*h*s+g*r*p-t*m*p-u*r*f+t*h*f)*I,e[6]=(g*c*s-a*m*s-g*r*l+t*m*l+a*r*f-t*c*f)*I,e[7]=(a*h*s-u*c*s+u*r*l-t*h*l-a*r*p+t*c*p)*I,e[8]=y*I,e[9]=(g*d*s-u*x*s-g*n*p+t*x*p+u*n*f-t*d*f)*I,e[10]=(a*x*s-g*o*s+g*n*l-t*x*l-a*n*f+t*o*f)*I,e[11]=(u*o*s-a*d*s-u*n*l+t*d*l+a*n*p-t*o*p)*I,e[12]=C*I,e[13]=(u*x*r-g*d*r+g*n*h-t*x*h-u*n*m+t*d*m)*I,e[14]=(g*o*r-a*x*r-g*n*c+t*x*c+a*n*m-t*o*m)*I,e[15]=(a*d*r-u*o*r+u*n*c-t*d*c-a*n*h+t*o*h)*I,this}scale(e){let t=this.elements,n=e.x,r=e.y,s=e.z;return t[0]*=n,t[4]*=r,t[8]*=s,t[1]*=n,t[5]*=r,t[9]*=s,t[2]*=n,t[6]*=r,t[10]*=s,t[3]*=n,t[7]*=r,t[11]*=s,this}getMaxScaleOnAxis(){let e=this.elements,t=e[0]*e[0]+e[1]*e[1]+e[2]*e[2],n=e[4]*e[4]+e[5]*e[5]+e[6]*e[6],r=e[8]*e[8]+e[9]*e[9]+e[10]*e[10];return Math.sqrt(Math.max(t,n,r))}makeTranslation(e,t,n){return e.isVector3?this.set(1,0,0,e.x,0,1,0,e.y,0,0,1,e.z,0,0,0,1):this.set(1,0,0,e,0,1,0,t,0,0,1,n,0,0,0,1),this}makeRotationX(e){let t=Math.cos(e),n=Math.sin(e);return this.set(1,0,0,0,0,t,-n,0,0,n,t,0,0,0,0,1),this}makeRotationY(e){let t=Math.cos(e),n=Math.sin(e);return this.set(t,0,n,0,0,1,0,0,-n,0,t,0,0,0,0,1),this}makeRotationZ(e){let t=Math.cos(e),n=Math.sin(e);return this.set(t,-n,0,0,n,t,0,0,0,0,1,0,0,0,0,1),this}makeRotationAxis(e,t){let n=Math.cos(t),r=Math.sin(t),s=1-n,a=e.x,o=e.y,c=e.z,l=s*a,u=s*o;return this.set(l*a+n,l*o-r*c,l*c+r*o,0,l*o+r*c,u*o+n,u*c-r*a,0,l*c-r*o,u*c+r*a,s*c*c+n,0,0,0,0,1),this}makeScale(e,t,n){return this.set(e,0,0,0,0,t,0,0,0,0,n,0,0,0,0,1),this}makeShear(e,t,n,r,s,a){return this.set(1,n,s,0,e,1,a,0,t,r,1,0,0,0,0,1),this}compose(e,t,n){let r=this.elements,s=t._x,a=t._y,o=t._z,c=t._w,l=s+s,u=a+a,d=o+o,h=s*l,p=s*u,g=s*d,x=a*u,m=a*d,f=o*d,S=c*l,M=c*u,y=c*d,C=n.x,A=n.y,I=n.z;return r[0]=(1-(x+f))*C,r[1]=(p+y)*C,r[2]=(g-M)*C,r[3]=0,r[4]=(p-y)*A,r[5]=(1-(h+f))*A,r[6]=(m+S)*A,r[7]=0,r[8]=(g+M)*I,r[9]=(m-S)*I,r[10]=(1-(h+x))*I,r[11]=0,r[12]=e.x,r[13]=e.y,r[14]=e.z,r[15]=1,this}decompose(e,t,n){let r=this.elements,s=Zi.set(r[0],r[1],r[2]).length(),a=Zi.set(r[4],r[5],r[6]).length(),o=Zi.set(r[8],r[9],r[10]).length();this.determinant()<0&&(s=-s),e.x=r[12],e.y=r[13],e.z=r[14],xn.copy(this);let l=1/s,u=1/a,d=1/o;return xn.elements[0]*=l,xn.elements[1]*=l,xn.elements[2]*=l,xn.elements[4]*=u,xn.elements[5]*=u,xn.elements[6]*=u,xn.elements[8]*=d,xn.elements[9]*=d,xn.elements[10]*=d,t.setFromRotationMatrix(xn),n.x=s,n.y=a,n.z=o,this}makePerspective(e,t,n,r,s,a,o=vn,c=!1){let l=this.elements,u=2*s/(t-e),d=2*s/(n-r),h=(t+e)/(t-e),p=(n+r)/(n-r),g,x;if(c)g=s/(a-s),x=a*s/(a-s);else if(o===vn)g=-(a+s)/(a-s),x=-2*a*s/(a-s);else if(o===Vr)g=-a/(a-s),x=-a*s/(a-s);else throw new Error("THREE.Matrix4.makePerspective(): Invalid coordinate system: "+o);return l[0]=u,l[4]=0,l[8]=h,l[12]=0,l[1]=0,l[5]=d,l[9]=p,l[13]=0,l[2]=0,l[6]=0,l[10]=g,l[14]=x,l[3]=0,l[7]=0,l[11]=-1,l[15]=0,this}makeOrthographic(e,t,n,r,s,a,o=vn,c=!1){let l=this.elements,u=2/(t-e),d=2/(n-r),h=-(t+e)/(t-e),p=-(n+r)/(n-r),g,x;if(c)g=1/(a-s),x=a/(a-s);else if(o===vn)g=-2/(a-s),x=-(a+s)/(a-s);else if(o===Vr)g=-1/(a-s),x=-s/(a-s);else throw new Error("THREE.Matrix4.makeOrthographic(): Invalid coordinate system: "+o);return l[0]=u,l[4]=0,l[8]=0,l[12]=h,l[1]=0,l[5]=d,l[9]=0,l[13]=p,l[2]=0,l[6]=0,l[10]=g,l[14]=x,l[3]=0,l[7]=0,l[11]=0,l[15]=1,this}equals(e){let t=this.elements,n=e.elements;for(let r=0;r<16;r++)if(t[r]!==n[r])return!1;return!0}fromArray(e,t=0){for(let n=0;n<16;n++)this.elements[n]=e[n+t];return this}toArray(e=[],t=0){let n=this.elements;return e[t]=n[0],e[t+1]=n[1],e[t+2]=n[2],e[t+3]=n[3],e[t+4]=n[4],e[t+5]=n[5],e[t+6]=n[6],e[t+7]=n[7],e[t+8]=n[8],e[t+9]=n[9],e[t+10]=n[10],e[t+11]=n[11],e[t+12]=n[12],e[t+13]=n[13],e[t+14]=n[14],e[t+15]=n[15],e}},Zi=new D,xn=new ht,Zh=new D(0,0,0),Jh=new D(1,1,1),ni=new D,Fs=new D,jt=new D,Xc=new ht,$c=new Gt,en=class i{constructor(e=0,t=0,n=0,r=i.DEFAULT_ORDER){this.isEuler=!0,this._x=e,this._y=t,this._z=n,this._order=r}get x(){return this._x}set x(e){this._x=e,this._onChangeCallback()}get y(){return this._y}set y(e){this._y=e,this._onChangeCallback()}get z(){return this._z}set z(e){this._z=e,this._onChangeCallback()}get order(){return this._order}set order(e){this._order=e,this._onChangeCallback()}set(e,t,n,r=this._order){return this._x=e,this._y=t,this._z=n,this._order=r,this._onChangeCallback(),this}clone(){return new this.constructor(this._x,this._y,this._z,this._order)}copy(e){return this._x=e._x,this._y=e._y,this._z=e._z,this._order=e._order,this._onChangeCallback(),this}setFromRotationMatrix(e,t=this._order,n=!0){let r=e.elements,s=r[0],a=r[4],o=r[8],c=r[1],l=r[5],u=r[9],d=r[2],h=r[6],p=r[10];switch(t){case"XYZ":this._y=Math.asin(Ye(o,-1,1)),Math.abs(o)<.9999999?(this._x=Math.atan2(-u,p),this._z=Math.atan2(-a,s)):(this._x=Math.atan2(h,l),this._z=0);break;case"YXZ":this._x=Math.asin(-Ye(u,-1,1)),Math.abs(u)<.9999999?(this._y=Math.atan2(o,p),this._z=Math.atan2(c,l)):(this._y=Math.atan2(-d,s),this._z=0);break;case"ZXY":this._x=Math.asin(Ye(h,-1,1)),Math.abs(h)<.9999999?(this._y=Math.atan2(-d,p),this._z=Math.atan2(-a,l)):(this._y=0,this._z=Math.atan2(c,s));break;case"ZYX":this._y=Math.asin(-Ye(d,-1,1)),Math.abs(d)<.9999999?(this._x=Math.atan2(h,p),this._z=Math.atan2(c,s)):(this._x=0,this._z=Math.atan2(-a,l));break;case"YZX":this._z=Math.asin(Ye(c,-1,1)),Math.abs(c)<.9999999?(this._x=Math.atan2(-u,l),this._y=Math.atan2(-d,s)):(this._x=0,this._y=Math.atan2(o,p));break;case"XZY":this._z=Math.asin(-Ye(a,-1,1)),Math.abs(a)<.9999999?(this._x=Math.atan2(h,l),this._y=Math.atan2(o,s)):(this._x=Math.atan2(-u,p),this._y=0);break;default:console.warn("THREE.Euler: .setFromRotationMatrix() encountered an unknown order: "+t)}return this._order=t,n===!0&&this._onChangeCallback(),this}setFromQuaternion(e,t,n){return Xc.makeRotationFromQuaternion(e),this.setFromRotationMatrix(Xc,t,n)}setFromVector3(e,t=this._order){return this.set(e.x,e.y,e.z,t)}reorder(e){return $c.setFromEuler(this),this.setFromQuaternion($c,e)}equals(e){return e._x===this._x&&e._y===this._y&&e._z===this._z&&e._order===this._order}fromArray(e){return this._x=e[0],this._y=e[1],this._z=e[2],e[3]!==void 0&&(this._order=e[3]),this._onChangeCallback(),this}toArray(e=[],t=0){return e[t]=this._x,e[t+1]=this._y,e[t+2]=this._z,e[t+3]=this._order,e}_onChange(e){return this._onChangeCallback=e,this}_onChangeCallback(){}*[Symbol.iterator](){yield this._x,yield this._y,yield this._z,yield this._order}};en.DEFAULT_ORDER="XYZ";var Xr=class{constructor(){this.mask=1}set(e){this.mask=(1<<e|0)>>>0}enable(e){this.mask|=1<<e|0}enableAll(){this.mask=-1}toggle(e){this.mask^=1<<e|0}disable(e){this.mask&=~(1<<e|0)}disableAll(){this.mask=0}test(e){return(this.mask&e.mask)!==0}isEnabled(e){return(this.mask&(1<<e|0))!==0}},Kh=0,qc=new D,Ji=new Gt,Bn=new ht,Us=new D,Dr=new D,jh=new D,Qh=new Gt,Yc=new D(1,0,0),Zc=new D(0,1,0),Jc=new D(0,0,1),Kc={type:"added"},ef={type:"removed"},Ki={type:"childadded",child:null},nl={type:"childremoved",child:null},Mt=class i extends Wn{constructor(){super(),this.isObject3D=!0,Object.defineProperty(this,"id",{value:Kh++}),this.uuid=Hn(),this.name="",this.type="Object3D",this.parent=null,this.children=[],this.up=i.DEFAULT_UP.clone();let e=new D,t=new en,n=new Gt,r=new D(1,1,1);function s(){n.setFromEuler(t,!1)}function a(){t.setFromQuaternion(n,void 0,!1)}t._onChange(s),n._onChange(a),Object.defineProperties(this,{position:{configurable:!0,enumerable:!0,value:e},rotation:{configurable:!0,enumerable:!0,value:t},quaternion:{configurable:!0,enumerable:!0,value:n},scale:{configurable:!0,enumerable:!0,value:r},modelViewMatrix:{value:new ht},normalMatrix:{value:new ke}}),this.matrix=new ht,this.matrixWorld=new ht,this.matrixAutoUpdate=i.DEFAULT_MATRIX_AUTO_UPDATE,this.matrixWorldAutoUpdate=i.DEFAULT_MATRIX_WORLD_AUTO_UPDATE,this.matrixWorldNeedsUpdate=!1,this.layers=new Xr,this.visible=!0,this.castShadow=!1,this.receiveShadow=!1,this.frustumCulled=!0,this.renderOrder=0,this.animations=[],this.customDepthMaterial=void 0,this.customDistanceMaterial=void 0,this.userData={}}onBeforeShadow(){}onAfterShadow(){}onBeforeRender(){}onAfterRender(){}applyMatrix4(e){this.matrixAutoUpdate&&this.updateMatrix(),this.matrix.premultiply(e),this.matrix.decompose(this.position,this.quaternion,this.scale)}applyQuaternion(e){return this.quaternion.premultiply(e),this}setRotationFromAxisAngle(e,t){this.quaternion.setFromAxisAngle(e,t)}setRotationFromEuler(e){this.quaternion.setFromEuler(e,!0)}setRotationFromMatrix(e){this.quaternion.setFromRotationMatrix(e)}setRotationFromQuaternion(e){this.quaternion.copy(e)}rotateOnAxis(e,t){return Ji.setFromAxisAngle(e,t),this.quaternion.multiply(Ji),this}rotateOnWorldAxis(e,t){return Ji.setFromAxisAngle(e,t),this.quaternion.premultiply(Ji),this}rotateX(e){return this.rotateOnAxis(Yc,e)}rotateY(e){return this.rotateOnAxis(Zc,e)}rotateZ(e){return this.rotateOnAxis(Jc,e)}translateOnAxis(e,t){return qc.copy(e).applyQuaternion(this.quaternion),this.position.add(qc.multiplyScalar(t)),this}translateX(e){return this.translateOnAxis(Yc,e)}translateY(e){return this.translateOnAxis(Zc,e)}translateZ(e){return this.translateOnAxis(Jc,e)}localToWorld(e){return this.updateWorldMatrix(!0,!1),e.applyMatrix4(this.matrixWorld)}worldToLocal(e){return this.updateWorldMatrix(!0,!1),e.applyMatrix4(Bn.copy(this.matrixWorld).invert())}lookAt(e,t,n){e.isVector3?Us.copy(e):Us.set(e,t,n);let r=this.parent;this.updateWorldMatrix(!0,!1),Dr.setFromMatrixPosition(this.matrixWorld),this.isCamera||this.isLight?Bn.lookAt(Dr,Us,this.up):Bn.lookAt(Us,Dr,this.up),this.quaternion.setFromRotationMatrix(Bn),r&&(Bn.extractRotation(r.matrixWorld),Ji.setFromRotationMatrix(Bn),this.quaternion.premultiply(Ji.invert()))}add(e){if(arguments.length>1){for(let t=0;t<arguments.length;t++)this.add(arguments[t]);return this}return e===this?(console.error("THREE.Object3D.add: object can't be added as a child of itself.",e),this):(e&&e.isObject3D?(e.removeFromParent(),e.parent=this,this.children.push(e),e.dispatchEvent(Kc),Ki.child=e,this.dispatchEvent(Ki),Ki.child=null):console.error("THREE.Object3D.add: object not an instance of THREE.Object3D.",e),this)}remove(e){if(arguments.length>1){for(let n=0;n<arguments.length;n++)this.remove(arguments[n]);return this}let t=this.children.indexOf(e);return t!==-1&&(e.parent=null,this.children.splice(t,1),e.dispatchEvent(ef),nl.child=e,this.dispatchEvent(nl),nl.child=null),this}removeFromParent(){let e=this.parent;return e!==null&&e.remove(this),this}clear(){return this.remove(...this.children)}attach(e){return this.updateWorldMatrix(!0,!1),Bn.copy(this.matrixWorld).invert(),e.parent!==null&&(e.parent.updateWorldMatrix(!0,!1),Bn.multiply(e.parent.matrixWorld)),e.applyMatrix4(Bn),e.removeFromParent(),e.parent=this,this.children.push(e),e.updateWorldMatrix(!1,!0),e.dispatchEvent(Kc),Ki.child=e,this.dispatchEvent(Ki),Ki.child=null,this}getObjectById(e){return this.getObjectByProperty("id",e)}getObjectByName(e){return this.getObjectByProperty("name",e)}getObjectByProperty(e,t){if(this[e]===t)return this;for(let n=0,r=this.children.length;n<r;n++){let a=this.children[n].getObjectByProperty(e,t);if(a!==void 0)return a}}getObjectsByProperty(e,t,n=[]){this[e]===t&&n.push(this);let r=this.children;for(let s=0,a=r.length;s<a;s++)r[s].getObjectsByProperty(e,t,n);return n}getWorldPosition(e){return this.updateWorldMatrix(!0,!1),e.setFromMatrixPosition(this.matrixWorld)}getWorldQuaternion(e){return this.updateWorldMatrix(!0,!1),this.matrixWorld.decompose(Dr,e,jh),e}getWorldScale(e){return this.updateWorldMatrix(!0,!1),this.matrixWorld.decompose(Dr,Qh,e),e}getWorldDirection(e){this.updateWorldMatrix(!0,!1);let t=this.matrixWorld.elements;return e.set(t[8],t[9],t[10]).normalize()}raycast(){}traverse(e){e(this);let t=this.children;for(let n=0,r=t.length;n<r;n++)t[n].traverse(e)}traverseVisible(e){if(this.visible===!1)return;e(this);let t=this.children;for(let n=0,r=t.length;n<r;n++)t[n].traverseVisible(e)}traverseAncestors(e){let t=this.parent;t!==null&&(e(t),t.traverseAncestors(e))}updateMatrix(){this.matrix.compose(this.position,this.quaternion,this.scale),this.matrixWorldNeedsUpdate=!0}updateMatrixWorld(e){this.matrixAutoUpdate&&this.updateMatrix(),(this.matrixWorldNeedsUpdate||e)&&(this.matrixWorldAutoUpdate===!0&&(this.parent===null?this.matrixWorld.copy(this.matrix):this.matrixWorld.multiplyMatrices(this.parent.matrixWorld,this.matrix)),this.matrixWorldNeedsUpdate=!1,e=!0);let t=this.children;for(let n=0,r=t.length;n<r;n++)t[n].updateMatrixWorld(e)}updateWorldMatrix(e,t){let n=this.parent;if(e===!0&&n!==null&&n.updateWorldMatrix(!0,!1),this.matrixAutoUpdate&&this.updateMatrix(),this.matrixWorldAutoUpdate===!0&&(this.parent===null?this.matrixWorld.copy(this.matrix):this.matrixWorld.multiplyMatrices(this.parent.matrixWorld,this.matrix)),t===!0){let r=this.children;for(let s=0,a=r.length;s<a;s++)r[s].updateWorldMatrix(!1,!0)}}toJSON(e){let t=e===void 0||typeof e=="string",n={};t&&(e={geometries:{},materials:{},textures:{},images:{},shapes:{},skeletons:{},animations:{},nodes:{}},n.metadata={version:4.7,type:"Object",generator:"Object3D.toJSON"});let r={};r.uuid=this.uuid,r.type=this.type,this.name!==""&&(r.name=this.name),this.castShadow===!0&&(r.castShadow=!0),this.receiveShadow===!0&&(r.receiveShadow=!0),this.visible===!1&&(r.visible=!1),this.frustumCulled===!1&&(r.frustumCulled=!1),this.renderOrder!==0&&(r.renderOrder=this.renderOrder),Object.keys(this.userData).length>0&&(r.userData=this.userData),r.layers=this.layers.mask,r.matrix=this.matrix.toArray(),r.up=this.up.toArray(),this.matrixAutoUpdate===!1&&(r.matrixAutoUpdate=!1),this.isInstancedMesh&&(r.type="InstancedMesh",r.count=this.count,r.instanceMatrix=this.instanceMatrix.toJSON(),this.instanceColor!==null&&(r.instanceColor=this.instanceColor.toJSON())),this.isBatchedMesh&&(r.type="BatchedMesh",r.perObjectFrustumCulled=this.perObjectFrustumCulled,r.sortObjects=this.sortObjects,r.drawRanges=this._drawRanges,r.reservedRanges=this._reservedRanges,r.geometryInfo=this._geometryInfo.map(o=>({...o,boundingBox:o.boundingBox?o.boundingBox.toJSON():void 0,boundingSphere:o.boundingSphere?o.boundingSphere.toJSON():void 0})),r.instanceInfo=this._instanceInfo.map(o=>({...o})),r.availableInstanceIds=this._availableInstanceIds.slice(),r.availableGeometryIds=this._availableGeometryIds.slice(),r.nextIndexStart=this._nextIndexStart,r.nextVertexStart=this._nextVertexStart,r.geometryCount=this._geometryCount,r.maxInstanceCount=this._maxInstanceCount,r.maxVertexCount=this._maxVertexCount,r.maxIndexCount=this._maxIndexCount,r.geometryInitialized=this._geometryInitialized,r.matricesTexture=this._matricesTexture.toJSON(e),r.indirectTexture=this._indirectTexture.toJSON(e),this._colorsTexture!==null&&(r.colorsTexture=this._colorsTexture.toJSON(e)),this.boundingSphere!==null&&(r.boundingSphere=this.boundingSphere.toJSON()),this.boundingBox!==null&&(r.boundingBox=this.boundingBox.toJSON()));function s(o,c){return o[c.uuid]===void 0&&(o[c.uuid]=c.toJSON(e)),c.uuid}if(this.isScene)this.background&&(this.background.isColor?r.background=this.background.toJSON():this.background.isTexture&&(r.background=this.background.toJSON(e).uuid)),this.environment&&this.environment.isTexture&&this.environment.isRenderTargetTexture!==!0&&(r.environment=this.environment.toJSON(e).uuid);else if(this.isMesh||this.isLine||this.isPoints){r.geometry=s(e.geometries,this.geometry);let o=this.geometry.parameters;if(o!==void 0&&o.shapes!==void 0){let c=o.shapes;if(Array.isArray(c))for(let l=0,u=c.length;l<u;l++){let d=c[l];s(e.shapes,d)}else s(e.shapes,c)}}if(this.isSkinnedMesh&&(r.bindMode=this.bindMode,r.bindMatrix=this.bindMatrix.toArray(),this.skeleton!==void 0&&(s(e.skeletons,this.skeleton),r.skeleton=this.skeleton.uuid)),this.material!==void 0)if(Array.isArray(this.material)){let o=[];for(let c=0,l=this.material.length;c<l;c++)o.push(s(e.materials,this.material[c]));r.material=o}else r.material=s(e.materials,this.material);if(this.children.length>0){r.children=[];for(let o=0;o<this.children.length;o++)r.children.push(this.children[o].toJSON(e).object)}if(this.animations.length>0){r.animations=[];for(let o=0;o<this.animations.length;o++){let c=this.animations[o];r.animations.push(s(e.animations,c))}}if(t){let o=a(e.geometries),c=a(e.materials),l=a(e.textures),u=a(e.images),d=a(e.shapes),h=a(e.skeletons),p=a(e.animations),g=a(e.nodes);o.length>0&&(n.geometries=o),c.length>0&&(n.materials=c),l.length>0&&(n.textures=l),u.length>0&&(n.images=u),d.length>0&&(n.shapes=d),h.length>0&&(n.skeletons=h),p.length>0&&(n.animations=p),g.length>0&&(n.nodes=g)}return n.object=r,n;function a(o){let c=[];for(let l in o){let u=o[l];delete u.metadata,c.push(u)}return c}}clone(e){return new this.constructor().copy(this,e)}copy(e,t=!0){if(this.name=e.name,this.up.copy(e.up),this.position.copy(e.position),this.rotation.order=e.rotation.order,this.quaternion.copy(e.quaternion),this.scale.copy(e.scale),this.matrix.copy(e.matrix),this.matrixWorld.copy(e.matrixWorld),this.matrixAutoUpdate=e.matrixAutoUpdate,this.matrixWorldAutoUpdate=e.matrixWorldAutoUpdate,this.matrixWorldNeedsUpdate=e.matrixWorldNeedsUpdate,this.layers.mask=e.layers.mask,this.visible=e.visible,this.castShadow=e.castShadow,this.receiveShadow=e.receiveShadow,this.frustumCulled=e.frustumCulled,this.renderOrder=e.renderOrder,this.animations=e.animations.slice(),this.userData=JSON.parse(JSON.stringify(e.userData)),t===!0)for(let n=0;n<e.children.length;n++){let r=e.children[n];this.add(r.clone())}return this}};Mt.DEFAULT_UP=new D(0,1,0);Mt.DEFAULT_MATRIX_AUTO_UPDATE=!0;Mt.DEFAULT_MATRIX_WORLD_AUTO_UPDATE=!0;var _n=new D,zn=new D,il=new D,kn=new D,ji=new D,Qi=new D,jc=new D,rl=new D,sl=new D,al=new D,ol=new xt,ll=new xt,cl=new xt,Cn=class i{constructor(e=new D,t=new D,n=new D){this.a=e,this.b=t,this.c=n}static getNormal(e,t,n,r){r.subVectors(n,t),_n.subVectors(e,t),r.cross(_n);let s=r.lengthSq();return s>0?r.multiplyScalar(1/Math.sqrt(s)):r.set(0,0,0)}static getBarycoord(e,t,n,r,s){_n.subVectors(r,t),zn.subVectors(n,t),il.subVectors(e,t);let a=_n.dot(_n),o=_n.dot(zn),c=_n.dot(il),l=zn.dot(zn),u=zn.dot(il),d=a*l-o*o;if(d===0)return s.set(0,0,0),null;let h=1/d,p=(l*c-o*u)*h,g=(a*u-o*c)*h;return s.set(1-p-g,g,p)}static containsPoint(e,t,n,r){return this.getBarycoord(e,t,n,r,kn)===null?!1:kn.x>=0&&kn.y>=0&&kn.x+kn.y<=1}static getInterpolation(e,t,n,r,s,a,o,c){return this.getBarycoord(e,t,n,r,kn)===null?(c.x=0,c.y=0,"z"in c&&(c.z=0),"w"in c&&(c.w=0),null):(c.setScalar(0),c.addScaledVector(s,kn.x),c.addScaledVector(a,kn.y),c.addScaledVector(o,kn.z),c)}static getInterpolatedAttribute(e,t,n,r,s,a){return ol.setScalar(0),ll.setScalar(0),cl.setScalar(0),ol.fromBufferAttribute(e,t),ll.fromBufferAttribute(e,n),cl.fromBufferAttribute(e,r),a.setScalar(0),a.addScaledVector(ol,s.x),a.addScaledVector(ll,s.y),a.addScaledVector(cl,s.z),a}static isFrontFacing(e,t,n,r){return _n.subVectors(n,t),zn.subVectors(e,t),_n.cross(zn).dot(r)<0}set(e,t,n){return this.a.copy(e),this.b.copy(t),this.c.copy(n),this}setFromPointsAndIndices(e,t,n,r){return this.a.copy(e[t]),this.b.copy(e[n]),this.c.copy(e[r]),this}setFromAttributeAndIndices(e,t,n,r){return this.a.fromBufferAttribute(e,t),this.b.fromBufferAttribute(e,n),this.c.fromBufferAttribute(e,r),this}clone(){return new this.constructor().copy(this)}copy(e){return this.a.copy(e.a),this.b.copy(e.b),this.c.copy(e.c),this}getArea(){return _n.subVectors(this.c,this.b),zn.subVectors(this.a,this.b),_n.cross(zn).length()*.5}getMidpoint(e){return e.addVectors(this.a,this.b).add(this.c).multiplyScalar(1/3)}getNormal(e){return i.getNormal(this.a,this.b,this.c,e)}getPlane(e){return e.setFromCoplanarPoints(this.a,this.b,this.c)}getBarycoord(e,t){return i.getBarycoord(e,this.a,this.b,this.c,t)}getInterpolation(e,t,n,r,s){return i.getInterpolation(e,this.a,this.b,this.c,t,n,r,s)}containsPoint(e){return i.containsPoint(e,this.a,this.b,this.c)}isFrontFacing(e){return i.isFrontFacing(this.a,this.b,this.c,e)}intersectsBox(e){return e.intersectsTriangle(this)}closestPointToPoint(e,t){let n=this.a,r=this.b,s=this.c,a,o;ji.subVectors(r,n),Qi.subVectors(s,n),rl.subVectors(e,n);let c=ji.dot(rl),l=Qi.dot(rl);if(c<=0&&l<=0)return t.copy(n);sl.subVectors(e,r);let u=ji.dot(sl),d=Qi.dot(sl);if(u>=0&&d<=u)return t.copy(r);let h=c*d-u*l;if(h<=0&&c>=0&&u<=0)return a=c/(c-u),t.copy(n).addScaledVector(ji,a);al.subVectors(e,s);let p=ji.dot(al),g=Qi.dot(al);if(g>=0&&p<=g)return t.copy(s);let x=p*l-c*g;if(x<=0&&l>=0&&g<=0)return o=l/(l-g),t.copy(n).addScaledVector(Qi,o);let m=u*g-p*d;if(m<=0&&d-u>=0&&p-g>=0)return jc.subVectors(s,r),o=(d-u)/(d-u+(p-g)),t.copy(r).addScaledVector(jc,o);let f=1/(m+x+h);return a=x*f,o=h*f,t.copy(n).addScaledVector(ji,a).addScaledVector(Qi,o)}equals(e){return e.a.equals(this.a)&&e.b.equals(this.b)&&e.c.equals(this.c)}},ru={aliceblue:15792383,antiquewhite:16444375,aqua:65535,aquamarine:8388564,azure:15794175,beige:16119260,bisque:16770244,black:0,blanchedalmond:16772045,blue:255,blueviolet:9055202,brown:10824234,burlywood:14596231,cadetblue:6266528,chartreuse:8388352,chocolate:13789470,coral:16744272,cornflowerblue:6591981,cornsilk:16775388,crimson:14423100,cyan:65535,darkblue:139,darkcyan:35723,darkgoldenrod:12092939,darkgray:11119017,darkgreen:25600,darkgrey:11119017,darkkhaki:12433259,darkmagenta:9109643,darkolivegreen:5597999,darkorange:16747520,darkorchid:10040012,darkred:9109504,darksalmon:15308410,darkseagreen:9419919,darkslateblue:4734347,darkslategray:3100495,darkslategrey:3100495,darkturquoise:52945,darkviolet:9699539,deeppink:16716947,deepskyblue:49151,dimgray:6908265,dimgrey:6908265,dodgerblue:2003199,firebrick:11674146,floralwhite:16775920,forestgreen:2263842,fuchsia:16711935,gainsboro:14474460,ghostwhite:16316671,gold:16766720,goldenrod:14329120,gray:8421504,green:32768,greenyellow:11403055,grey:8421504,honeydew:15794160,hotpink:16738740,indianred:13458524,indigo:4915330,ivory:16777200,khaki:15787660,lavender:15132410,lavenderblush:16773365,lawngreen:8190976,lemonchiffon:16775885,lightblue:11393254,lightcoral:15761536,lightcyan:14745599,lightgoldenrodyellow:16448210,lightgray:13882323,lightgreen:9498256,lightgrey:13882323,lightpink:16758465,lightsalmon:16752762,lightseagreen:2142890,lightskyblue:8900346,lightslategray:7833753,lightslategrey:7833753,lightsteelblue:11584734,lightyellow:16777184,lime:65280,limegreen:3329330,linen:16445670,magenta:16711935,maroon:8388608,mediumaquamarine:6737322,mediumblue:205,mediumorchid:12211667,mediumpurple:9662683,mediumseagreen:3978097,mediumslateblue:8087790,mediumspringgreen:64154,mediumturquoise:4772300,mediumvioletred:13047173,midnightblue:1644912,mintcream:16121850,mistyrose:16770273,moccasin:16770229,navajowhite:16768685,navy:128,oldlace:16643558,olive:8421376,olivedrab:7048739,orange:16753920,orangered:16729344,orchid:14315734,palegoldenrod:15657130,palegreen:10025880,paleturquoise:11529966,palevioletred:14381203,papayawhip:16773077,peachpuff:16767673,peru:13468991,pink:16761035,plum:14524637,powderblue:11591910,purple:8388736,rebeccapurple:6697881,red:16711680,rosybrown:12357519,royalblue:4286945,saddlebrown:9127187,salmon:16416882,sandybrown:16032864,seagreen:3050327,seashell:16774638,sienna:10506797,silver:12632256,skyblue:8900331,slateblue:6970061,slategray:7372944,slategrey:7372944,snow:16775930,springgreen:65407,steelblue:4620980,tan:13808780,teal:32896,thistle:14204888,tomato:16737095,turquoise:4251856,violet:15631086,wheat:16113331,white:16777215,whitesmoke:16119285,yellow:16776960,yellowgreen:10145074},ii={h:0,s:0,l:0},Os={h:0,s:0,l:0};function dl(i,e,t){return t<0&&(t+=1),t>1&&(t-=1),t<1/6?i+(e-i)*6*t:t<1/2?e:t<2/3?i+(e-i)*6*(2/3-t):i}var Be=class{constructor(e,t,n){return this.isColor=!0,this.r=1,this.g=1,this.b=1,this.set(e,t,n)}set(e,t,n){if(t===void 0&&n===void 0){let r=e;r&&r.isColor?this.copy(r):typeof r=="number"?this.setHex(r):typeof r=="string"&&this.setStyle(r)}else this.setRGB(e,t,n);return this}setScalar(e){return this.r=e,this.g=e,this.b=e,this}setHex(e,t=Nt){return e=Math.floor(e),this.r=(e>>16&255)/255,this.g=(e>>8&255)/255,this.b=(e&255)/255,Ke.colorSpaceToWorking(this,t),this}setRGB(e,t,n,r=Ke.workingColorSpace){return this.r=e,this.g=t,this.b=n,Ke.colorSpaceToWorking(this,r),this}setHSL(e,t,n,r=Ke.workingColorSpace){if(e=Xl(e,1),t=Ye(t,0,1),n=Ye(n,0,1),t===0)this.r=this.g=this.b=n;else{let s=n<=.5?n*(1+t):n+t-n*t,a=2*n-s;this.r=dl(a,s,e+1/3),this.g=dl(a,s,e),this.b=dl(a,s,e-1/3)}return Ke.colorSpaceToWorking(this,r),this}setStyle(e,t=Nt){function n(s){s!==void 0&&parseFloat(s)<1&&console.warn("THREE.Color: Alpha component of "+e+" will be ignored.")}let r;if(r=/^(\w+)\(([^\)]*)\)/.exec(e)){let s,a=r[1],o=r[2];switch(a){case"rgb":case"rgba":if(s=/^\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*(?:,\s*(\d*\.?\d+)\s*)?$/.exec(o))return n(s[4]),this.setRGB(Math.min(255,parseInt(s[1],10))/255,Math.min(255,parseInt(s[2],10))/255,Math.min(255,parseInt(s[3],10))/255,t);if(s=/^\s*(\d+)\%\s*,\s*(\d+)\%\s*,\s*(\d+)\%\s*(?:,\s*(\d*\.?\d+)\s*)?$/.exec(o))return n(s[4]),this.setRGB(Math.min(100,parseInt(s[1],10))/100,Math.min(100,parseInt(s[2],10))/100,Math.min(100,parseInt(s[3],10))/100,t);break;case"hsl":case"hsla":if(s=/^\s*(\d*\.?\d+)\s*,\s*(\d*\.?\d+)\%\s*,\s*(\d*\.?\d+)\%\s*(?:,\s*(\d*\.?\d+)\s*)?$/.exec(o))return n(s[4]),this.setHSL(parseFloat(s[1])/360,parseFloat(s[2])/100,parseFloat(s[3])/100,t);break;default:console.warn("THREE.Color: Unknown color model "+e)}}else if(r=/^\#([A-Fa-f\d]+)$/.exec(e)){let s=r[1],a=s.length;if(a===3)return this.setRGB(parseInt(s.charAt(0),16)/15,parseInt(s.charAt(1),16)/15,parseInt(s.charAt(2),16)/15,t);if(a===6)return this.setHex(parseInt(s,16),t);console.warn("THREE.Color: Invalid hex color "+e)}else if(e&&e.length>0)return this.setColorName(e,t);return this}setColorName(e,t=Nt){let n=ru[e.toLowerCase()];return n!==void 0?this.setHex(n,t):console.warn("THREE.Color: Unknown color "+e),this}clone(){return new this.constructor(this.r,this.g,this.b)}copy(e){return this.r=e.r,this.g=e.g,this.b=e.b,this}copySRGBToLinear(e){return this.r=Vn(e.r),this.g=Vn(e.g),this.b=Vn(e.b),this}copyLinearToSRGB(e){return this.r=lr(e.r),this.g=lr(e.g),this.b=lr(e.b),this}convertSRGBToLinear(){return this.copySRGBToLinear(this),this}convertLinearToSRGB(){return this.copyLinearToSRGB(this),this}getHex(e=Nt){return Ke.workingToColorSpace(Pt.copy(this),e),Math.round(Ye(Pt.r*255,0,255))*65536+Math.round(Ye(Pt.g*255,0,255))*256+Math.round(Ye(Pt.b*255,0,255))}getHexString(e=Nt){return("000000"+this.getHex(e).toString(16)).slice(-6)}getHSL(e,t=Ke.workingColorSpace){Ke.workingToColorSpace(Pt.copy(this),t);let n=Pt.r,r=Pt.g,s=Pt.b,a=Math.max(n,r,s),o=Math.min(n,r,s),c,l,u=(o+a)/2;if(o===a)c=0,l=0;else{let d=a-o;switch(l=u<=.5?d/(a+o):d/(2-a-o),a){case n:c=(r-s)/d+(r<s?6:0);break;case r:c=(s-n)/d+2;break;case s:c=(n-r)/d+4;break}c/=6}return e.h=c,e.s=l,e.l=u,e}getRGB(e,t=Ke.workingColorSpace){return Ke.workingToColorSpace(Pt.copy(this),t),e.r=Pt.r,e.g=Pt.g,e.b=Pt.b,e}getStyle(e=Nt){Ke.workingToColorSpace(Pt.copy(this),e);let t=Pt.r,n=Pt.g,r=Pt.b;return e!==Nt?`color(${e} ${t.toFixed(3)} ${n.toFixed(3)} ${r.toFixed(3)})`:`rgb(${Math.round(t*255)},${Math.round(n*255)},${Math.round(r*255)})`}offsetHSL(e,t,n){return this.getHSL(ii),this.setHSL(ii.h+e,ii.s+t,ii.l+n)}add(e){return this.r+=e.r,this.g+=e.g,this.b+=e.b,this}addColors(e,t){return this.r=e.r+t.r,this.g=e.g+t.g,this.b=e.b+t.b,this}addScalar(e){return this.r+=e,this.g+=e,this.b+=e,this}sub(e){return this.r=Math.max(0,this.r-e.r),this.g=Math.max(0,this.g-e.g),this.b=Math.max(0,this.b-e.b),this}multiply(e){return this.r*=e.r,this.g*=e.g,this.b*=e.b,this}multiplyScalar(e){return this.r*=e,this.g*=e,this.b*=e,this}lerp(e,t){return this.r+=(e.r-this.r)*t,this.g+=(e.g-this.g)*t,this.b+=(e.b-this.b)*t,this}lerpColors(e,t,n){return this.r=e.r+(t.r-e.r)*n,this.g=e.g+(t.g-e.g)*n,this.b=e.b+(t.b-e.b)*n,this}lerpHSL(e,t){this.getHSL(ii),e.getHSL(Os);let n=zr(ii.h,Os.h,t),r=zr(ii.s,Os.s,t),s=zr(ii.l,Os.l,t);return this.setHSL(n,r,s),this}setFromVector3(e){return this.r=e.x,this.g=e.y,this.b=e.z,this}applyMatrix3(e){let t=this.r,n=this.g,r=this.b,s=e.elements;return this.r=s[0]*t+s[3]*n+s[6]*r,this.g=s[1]*t+s[4]*n+s[7]*r,this.b=s[2]*t+s[5]*n+s[8]*r,this}equals(e){return e.r===this.r&&e.g===this.g&&e.b===this.b}fromArray(e,t=0){return this.r=e[t],this.g=e[t+1],this.b=e[t+2],this}toArray(e=[],t=0){return e[t]=this.r,e[t+1]=this.g,e[t+2]=this.b,e}fromBufferAttribute(e,t){return this.r=e.getX(t),this.g=e.getY(t),this.b=e.getZ(t),this}toJSON(){return this.getHex()}*[Symbol.iterator](){yield this.r,yield this.g,yield this.b}},Pt=new Be;Be.NAMES=ru;var tf=0,wn=class extends Wn{constructor(){super(),this.isMaterial=!0,Object.defineProperty(this,"id",{value:tf++}),this.uuid=Hn(),this.name="",this.type="Material",this.blending=Si,this.side=Gn,this.vertexColors=!1,this.opacity=1,this.transparent=!1,this.alphaHash=!1,this.blendSrc=aa,this.blendDst=oa,this.blendEquation=ai,this.blendSrcAlpha=null,this.blendDstAlpha=null,this.blendEquationAlpha=null,this.blendColor=new Be(0,0,0),this.blendAlpha=0,this.depthFunc=Ei,this.depthTest=!0,this.depthWrite=!0,this.stencilWriteMask=255,this.stencilFunc=wl,this.stencilRef=0,this.stencilFuncMask=255,this.stencilFail=Mi,this.stencilZFail=Mi,this.stencilZPass=Mi,this.stencilWrite=!1,this.clippingPlanes=null,this.clipIntersection=!1,this.clipShadows=!1,this.shadowSide=null,this.colorWrite=!0,this.precision=null,this.polygonOffset=!1,this.polygonOffsetFactor=0,this.polygonOffsetUnits=0,this.dithering=!1,this.alphaToCoverage=!1,this.premultipliedAlpha=!1,this.forceSinglePass=!1,this.allowOverride=!0,this.visible=!0,this.toneMapped=!0,this.userData={},this.version=0,this._alphaTest=0}get alphaTest(){return this._alphaTest}set alphaTest(e){this._alphaTest>0!=e>0&&this.version++,this._alphaTest=e}onBeforeRender(){}onBeforeCompile(){}customProgramCacheKey(){return this.onBeforeCompile.toString()}setValues(e){if(e!==void 0)for(let t in e){let n=e[t];if(n===void 0){console.warn(`THREE.Material: parameter '${t}' has value of undefined.`);continue}let r=this[t];if(r===void 0){console.warn(`THREE.Material: '${t}' is not a property of THREE.${this.type}.`);continue}r&&r.isColor?r.set(n):r&&r.isVector3&&n&&n.isVector3?r.copy(n):this[t]=n}}toJSON(e){let t=e===void 0||typeof e=="string";t&&(e={textures:{},images:{}});let n={metadata:{version:4.7,type:"Material",generator:"Material.toJSON"}};n.uuid=this.uuid,n.type=this.type,this.name!==""&&(n.name=this.name),this.color&&this.color.isColor&&(n.color=this.color.getHex()),this.roughness!==void 0&&(n.roughness=this.roughness),this.metalness!==void 0&&(n.metalness=this.metalness),this.sheen!==void 0&&(n.sheen=this.sheen),this.sheenColor&&this.sheenColor.isColor&&(n.sheenColor=this.sheenColor.getHex()),this.sheenRoughness!==void 0&&(n.sheenRoughness=this.sheenRoughness),this.emissive&&this.emissive.isColor&&(n.emissive=this.emissive.getHex()),this.emissiveIntensity!==void 0&&this.emissiveIntensity!==1&&(n.emissiveIntensity=this.emissiveIntensity),this.specular&&this.specular.isColor&&(n.specular=this.specular.getHex()),this.specularIntensity!==void 0&&(n.specularIntensity=this.specularIntensity),this.specularColor&&this.specularColor.isColor&&(n.specularColor=this.specularColor.getHex()),this.shininess!==void 0&&(n.shininess=this.shininess),this.clearcoat!==void 0&&(n.clearcoat=this.clearcoat),this.clearcoatRoughness!==void 0&&(n.clearcoatRoughness=this.clearcoatRoughness),this.clearcoatMap&&this.clearcoatMap.isTexture&&(n.clearcoatMap=this.clearcoatMap.toJSON(e).uuid),this.clearcoatRoughnessMap&&this.clearcoatRoughnessMap.isTexture&&(n.clearcoatRoughnessMap=this.clearcoatRoughnessMap.toJSON(e).uuid),this.clearcoatNormalMap&&this.clearcoatNormalMap.isTexture&&(n.clearcoatNormalMap=this.clearcoatNormalMap.toJSON(e).uuid,n.clearcoatNormalScale=this.clearcoatNormalScale.toArray()),this.sheenColorMap&&this.sheenColorMap.isTexture&&(n.sheenColorMap=this.sheenColorMap.toJSON(e).uuid),this.sheenRoughnessMap&&this.sheenRoughnessMap.isTexture&&(n.sheenRoughnessMap=this.sheenRoughnessMap.toJSON(e).uuid),this.dispersion!==void 0&&(n.dispersion=this.dispersion),this.iridescence!==void 0&&(n.iridescence=this.iridescence),this.iridescenceIOR!==void 0&&(n.iridescenceIOR=this.iridescenceIOR),this.iridescenceThicknessRange!==void 0&&(n.iridescenceThicknessRange=this.iridescenceThicknessRange),this.iridescenceMap&&this.iridescenceMap.isTexture&&(n.iridescenceMap=this.iridescenceMap.toJSON(e).uuid),this.iridescenceThicknessMap&&this.iridescenceThicknessMap.isTexture&&(n.iridescenceThicknessMap=this.iridescenceThicknessMap.toJSON(e).uuid),this.anisotropy!==void 0&&(n.anisotropy=this.anisotropy),this.anisotropyRotation!==void 0&&(n.anisotropyRotation=this.anisotropyRotation),this.anisotropyMap&&this.anisotropyMap.isTexture&&(n.anisotropyMap=this.anisotropyMap.toJSON(e).uuid),this.map&&this.map.isTexture&&(n.map=this.map.toJSON(e).uuid),this.matcap&&this.matcap.isTexture&&(n.matcap=this.matcap.toJSON(e).uuid),this.alphaMap&&this.alphaMap.isTexture&&(n.alphaMap=this.alphaMap.toJSON(e).uuid),this.lightMap&&this.lightMap.isTexture&&(n.lightMap=this.lightMap.toJSON(e).uuid,n.lightMapIntensity=this.lightMapIntensity),this.aoMap&&this.aoMap.isTexture&&(n.aoMap=this.aoMap.toJSON(e).uuid,n.aoMapIntensity=this.aoMapIntensity),this.bumpMap&&this.bumpMap.isTexture&&(n.bumpMap=this.bumpMap.toJSON(e).uuid,n.bumpScale=this.bumpScale),this.normalMap&&this.normalMap.isTexture&&(n.normalMap=this.normalMap.toJSON(e).uuid,n.normalMapType=this.normalMapType,n.normalScale=this.normalScale.toArray()),this.displacementMap&&this.displacementMap.isTexture&&(n.displacementMap=this.displacementMap.toJSON(e).uuid,n.displacementScale=this.displacementScale,n.displacementBias=this.displacementBias),this.roughnessMap&&this.roughnessMap.isTexture&&(n.roughnessMap=this.roughnessMap.toJSON(e).uuid),this.metalnessMap&&this.metalnessMap.isTexture&&(n.metalnessMap=this.metalnessMap.toJSON(e).uuid),this.emissiveMap&&this.emissiveMap.isTexture&&(n.emissiveMap=this.emissiveMap.toJSON(e).uuid),this.specularMap&&this.specularMap.isTexture&&(n.specularMap=this.specularMap.toJSON(e).uuid),this.specularIntensityMap&&this.specularIntensityMap.isTexture&&(n.specularIntensityMap=this.specularIntensityMap.toJSON(e).uuid),this.specularColorMap&&this.specularColorMap.isTexture&&(n.specularColorMap=this.specularColorMap.toJSON(e).uuid),this.envMap&&this.envMap.isTexture&&(n.envMap=this.envMap.toJSON(e).uuid,this.combine!==void 0&&(n.combine=this.combine)),this.envMapRotation!==void 0&&(n.envMapRotation=this.envMapRotation.toArray()),this.envMapIntensity!==void 0&&(n.envMapIntensity=this.envMapIntensity),this.reflectivity!==void 0&&(n.reflectivity=this.reflectivity),this.refractionRatio!==void 0&&(n.refractionRatio=this.refractionRatio),this.gradientMap&&this.gradientMap.isTexture&&(n.gradientMap=this.gradientMap.toJSON(e).uuid),this.transmission!==void 0&&(n.transmission=this.transmission),this.transmissionMap&&this.transmissionMap.isTexture&&(n.transmissionMap=this.transmissionMap.toJSON(e).uuid),this.thickness!==void 0&&(n.thickness=this.thickness),this.thicknessMap&&this.thicknessMap.isTexture&&(n.thicknessMap=this.thicknessMap.toJSON(e).uuid),this.attenuationDistance!==void 0&&this.attenuationDistance!==1/0&&(n.attenuationDistance=this.attenuationDistance),this.attenuationColor!==void 0&&(n.attenuationColor=this.attenuationColor.getHex()),this.size!==void 0&&(n.size=this.size),this.shadowSide!==null&&(n.shadowSide=this.shadowSide),this.sizeAttenuation!==void 0&&(n.sizeAttenuation=this.sizeAttenuation),this.blending!==Si&&(n.blending=this.blending),this.side!==Gn&&(n.side=this.side),this.vertexColors===!0&&(n.vertexColors=!0),this.opacity<1&&(n.opacity=this.opacity),this.transparent===!0&&(n.transparent=!0),this.blendSrc!==aa&&(n.blendSrc=this.blendSrc),this.blendDst!==oa&&(n.blendDst=this.blendDst),this.blendEquation!==ai&&(n.blendEquation=this.blendEquation),this.blendSrcAlpha!==null&&(n.blendSrcAlpha=this.blendSrcAlpha),this.blendDstAlpha!==null&&(n.blendDstAlpha=this.blendDstAlpha),this.blendEquationAlpha!==null&&(n.blendEquationAlpha=this.blendEquationAlpha),this.blendColor&&this.blendColor.isColor&&(n.blendColor=this.blendColor.getHex()),this.blendAlpha!==0&&(n.blendAlpha=this.blendAlpha),this.depthFunc!==Ei&&(n.depthFunc=this.depthFunc),this.depthTest===!1&&(n.depthTest=this.depthTest),this.depthWrite===!1&&(n.depthWrite=this.depthWrite),this.colorWrite===!1&&(n.colorWrite=this.colorWrite),this.stencilWriteMask!==255&&(n.stencilWriteMask=this.stencilWriteMask),this.stencilFunc!==wl&&(n.stencilFunc=this.stencilFunc),this.stencilRef!==0&&(n.stencilRef=this.stencilRef),this.stencilFuncMask!==255&&(n.stencilFuncMask=this.stencilFuncMask),this.stencilFail!==Mi&&(n.stencilFail=this.stencilFail),this.stencilZFail!==Mi&&(n.stencilZFail=this.stencilZFail),this.stencilZPass!==Mi&&(n.stencilZPass=this.stencilZPass),this.stencilWrite===!0&&(n.stencilWrite=this.stencilWrite),this.rotation!==void 0&&this.rotation!==0&&(n.rotation=this.rotation),this.polygonOffset===!0&&(n.polygonOffset=!0),this.polygonOffsetFactor!==0&&(n.polygonOffsetFactor=this.polygonOffsetFactor),this.polygonOffsetUnits!==0&&(n.polygonOffsetUnits=this.polygonOffsetUnits),this.linewidth!==void 0&&this.linewidth!==1&&(n.linewidth=this.linewidth),this.dashSize!==void 0&&(n.dashSize=this.dashSize),this.gapSize!==void 0&&(n.gapSize=this.gapSize),this.scale!==void 0&&(n.scale=this.scale),this.dithering===!0&&(n.dithering=!0),this.alphaTest>0&&(n.alphaTest=this.alphaTest),this.alphaHash===!0&&(n.alphaHash=!0),this.alphaToCoverage===!0&&(n.alphaToCoverage=!0),this.premultipliedAlpha===!0&&(n.premultipliedAlpha=!0),this.forceSinglePass===!0&&(n.forceSinglePass=!0),this.wireframe===!0&&(n.wireframe=!0),this.wireframeLinewidth>1&&(n.wireframeLinewidth=this.wireframeLinewidth),this.wireframeLinecap!=="round"&&(n.wireframeLinecap=this.wireframeLinecap),this.wireframeLinejoin!=="round"&&(n.wireframeLinejoin=this.wireframeLinejoin),this.flatShading===!0&&(n.flatShading=!0),this.visible===!1&&(n.visible=!1),this.toneMapped===!1&&(n.toneMapped=!1),this.fog===!1&&(n.fog=!1),Object.keys(this.userData).length>0&&(n.userData=this.userData);function r(s){let a=[];for(let o in s){let c=s[o];delete c.metadata,a.push(c)}return a}if(t){let s=r(e.textures),a=r(e.images);s.length>0&&(n.textures=s),a.length>0&&(n.images=a)}return n}clone(){return new this.constructor().copy(this)}copy(e){this.name=e.name,this.blending=e.blending,this.side=e.side,this.vertexColors=e.vertexColors,this.opacity=e.opacity,this.transparent=e.transparent,this.blendSrc=e.blendSrc,this.blendDst=e.blendDst,this.blendEquation=e.blendEquation,this.blendSrcAlpha=e.blendSrcAlpha,this.blendDstAlpha=e.blendDstAlpha,this.blendEquationAlpha=e.blendEquationAlpha,this.blendColor.copy(e.blendColor),this.blendAlpha=e.blendAlpha,this.depthFunc=e.depthFunc,this.depthTest=e.depthTest,this.depthWrite=e.depthWrite,this.stencilWriteMask=e.stencilWriteMask,this.stencilFunc=e.stencilFunc,this.stencilRef=e.stencilRef,this.stencilFuncMask=e.stencilFuncMask,this.stencilFail=e.stencilFail,this.stencilZFail=e.stencilZFail,this.stencilZPass=e.stencilZPass,this.stencilWrite=e.stencilWrite;let t=e.clippingPlanes,n=null;if(t!==null){let r=t.length;n=new Array(r);for(let s=0;s!==r;++s)n[s]=t[s].clone()}return this.clippingPlanes=n,this.clipIntersection=e.clipIntersection,this.clipShadows=e.clipShadows,this.shadowSide=e.shadowSide,this.colorWrite=e.colorWrite,this.precision=e.precision,this.polygonOffset=e.polygonOffset,this.polygonOffsetFactor=e.polygonOffsetFactor,this.polygonOffsetUnits=e.polygonOffsetUnits,this.dithering=e.dithering,this.alphaTest=e.alphaTest,this.alphaHash=e.alphaHash,this.alphaToCoverage=e.alphaToCoverage,this.premultipliedAlpha=e.premultipliedAlpha,this.forceSinglePass=e.forceSinglePass,this.visible=e.visible,this.toneMapped=e.toneMapped,this.userData=JSON.parse(JSON.stringify(e.userData)),this}dispose(){this.dispatchEvent({type:"dispose"})}set needsUpdate(e){e===!0&&this.version++}},Wt=class extends wn{constructor(e){super(),this.isMeshBasicMaterial=!0,this.type="MeshBasicMaterial",this.color=new Be(16777215),this.map=null,this.lightMap=null,this.lightMapIntensity=1,this.aoMap=null,this.aoMapIntensity=1,this.specularMap=null,this.alphaMap=null,this.envMap=null,this.envMapRotation=new en,this.combine=Nl,this.reflectivity=1,this.refractionRatio=.98,this.wireframe=!1,this.wireframeLinewidth=1,this.wireframeLinecap="round",this.wireframeLinejoin="round",this.fog=!0,this.setValues(e)}copy(e){return super.copy(e),this.color.copy(e.color),this.map=e.map,this.lightMap=e.lightMap,this.lightMapIntensity=e.lightMapIntensity,this.aoMap=e.aoMap,this.aoMapIntensity=e.aoMapIntensity,this.specularMap=e.specularMap,this.alphaMap=e.alphaMap,this.envMap=e.envMap,this.envMapRotation.copy(e.envMapRotation),this.combine=e.combine,this.reflectivity=e.reflectivity,this.refractionRatio=e.refractionRatio,this.wireframe=e.wireframe,this.wireframeLinewidth=e.wireframeLinewidth,this.wireframeLinecap=e.wireframeLinecap,this.wireframeLinejoin=e.wireframeLinejoin,this.fog=e.fog,this}};var wt=new D,Bs=new We,nf=0,Vt=class{constructor(e,t,n=!1){if(Array.isArray(e))throw new TypeError("THREE.BufferAttribute: array should be a Typed Array.");this.isBufferAttribute=!0,Object.defineProperty(this,"id",{value:nf++}),this.name="",this.array=e,this.itemSize=t,this.count=e!==void 0?e.length/t:0,this.normalized=n,this.usage=ua,this.updateRanges=[],this.gpuType=Nn,this.version=0}onUploadCallback(){}set needsUpdate(e){e===!0&&this.version++}setUsage(e){return this.usage=e,this}addUpdateRange(e,t){this.updateRanges.push({start:e,count:t})}clearUpdateRanges(){this.updateRanges.length=0}copy(e){return this.name=e.name,this.array=new e.array.constructor(e.array),this.itemSize=e.itemSize,this.count=e.count,this.normalized=e.normalized,this.usage=e.usage,this.gpuType=e.gpuType,this}copyAt(e,t,n){e*=this.itemSize,n*=t.itemSize;for(let r=0,s=this.itemSize;r<s;r++)this.array[e+r]=t.array[n+r];return this}copyArray(e){return this.array.set(e),this}applyMatrix3(e){if(this.itemSize===2)for(let t=0,n=this.count;t<n;t++)Bs.fromBufferAttribute(this,t),Bs.applyMatrix3(e),this.setXY(t,Bs.x,Bs.y);else if(this.itemSize===3)for(let t=0,n=this.count;t<n;t++)wt.fromBufferAttribute(this,t),wt.applyMatrix3(e),this.setXYZ(t,wt.x,wt.y,wt.z);return this}applyMatrix4(e){for(let t=0,n=this.count;t<n;t++)wt.fromBufferAttribute(this,t),wt.applyMatrix4(e),this.setXYZ(t,wt.x,wt.y,wt.z);return this}applyNormalMatrix(e){for(let t=0,n=this.count;t<n;t++)wt.fromBufferAttribute(this,t),wt.applyNormalMatrix(e),this.setXYZ(t,wt.x,wt.y,wt.z);return this}transformDirection(e){for(let t=0,n=this.count;t<n;t++)wt.fromBufferAttribute(this,t),wt.transformDirection(e),this.setXYZ(t,wt.x,wt.y,wt.z);return this}set(e,t=0){return this.array.set(e,t),this}getComponent(e,t){let n=this.array[e*this.itemSize+t];return this.normalized&&(n=yn(n,this.array)),n}setComponent(e,t,n){return this.normalized&&(n=et(n,this.array)),this.array[e*this.itemSize+t]=n,this}getX(e){let t=this.array[e*this.itemSize];return this.normalized&&(t=yn(t,this.array)),t}setX(e,t){return this.normalized&&(t=et(t,this.array)),this.array[e*this.itemSize]=t,this}getY(e){let t=this.array[e*this.itemSize+1];return this.normalized&&(t=yn(t,this.array)),t}setY(e,t){return this.normalized&&(t=et(t,this.array)),this.array[e*this.itemSize+1]=t,this}getZ(e){let t=this.array[e*this.itemSize+2];return this.normalized&&(t=yn(t,this.array)),t}setZ(e,t){return this.normalized&&(t=et(t,this.array)),this.array[e*this.itemSize+2]=t,this}getW(e){let t=this.array[e*this.itemSize+3];return this.normalized&&(t=yn(t,this.array)),t}setW(e,t){return this.normalized&&(t=et(t,this.array)),this.array[e*this.itemSize+3]=t,this}setXY(e,t,n){return e*=this.itemSize,this.normalized&&(t=et(t,this.array),n=et(n,this.array)),this.array[e+0]=t,this.array[e+1]=n,this}setXYZ(e,t,n,r){return e*=this.itemSize,this.normalized&&(t=et(t,this.array),n=et(n,this.array),r=et(r,this.array)),this.array[e+0]=t,this.array[e+1]=n,this.array[e+2]=r,this}setXYZW(e,t,n,r,s){return e*=this.itemSize,this.normalized&&(t=et(t,this.array),n=et(n,this.array),r=et(r,this.array),s=et(s,this.array)),this.array[e+0]=t,this.array[e+1]=n,this.array[e+2]=r,this.array[e+3]=s,this}onUpload(e){return this.onUploadCallback=e,this}clone(){return new this.constructor(this.array,this.itemSize).copy(this)}toJSON(){let e={itemSize:this.itemSize,type:this.array.constructor.name,array:Array.from(this.array),normalized:this.normalized};return this.name!==""&&(e.name=this.name),this.usage!==ua&&(e.usage=this.usage),e}};var $r=class extends Vt{constructor(e,t,n){super(new Uint16Array(e),t,n)}};var qr=class extends Vt{constructor(e,t,n){super(new Uint32Array(e),t,n)}};var nt=class extends Vt{constructor(e,t,n){super(new Float32Array(e),t,n)}},rf=0,cn=new ht,ul=new Mt,er=new D,Qt=new oi,Lr=new oi,Ct=new D,ft=class i extends Wn{constructor(){super(),this.isBufferGeometry=!0,Object.defineProperty(this,"id",{value:rf++}),this.uuid=Hn(),this.name="",this.type="BufferGeometry",this.index=null,this.indirect=null,this.attributes={},this.morphAttributes={},this.morphTargetsRelative=!1,this.groups=[],this.boundingBox=null,this.boundingSphere=null,this.drawRange={start:0,count:1/0},this.userData={}}getIndex(){return this.index}setIndex(e){return Array.isArray(e)?this.index=new($l(e)?qr:$r)(e,1):this.index=e,this}setIndirect(e){return this.indirect=e,this}getIndirect(){return this.indirect}getAttribute(e){return this.attributes[e]}setAttribute(e,t){return this.attributes[e]=t,this}deleteAttribute(e){return delete this.attributes[e],this}hasAttribute(e){return this.attributes[e]!==void 0}addGroup(e,t,n=0){this.groups.push({start:e,count:t,materialIndex:n})}clearGroups(){this.groups=[]}setDrawRange(e,t){this.drawRange.start=e,this.drawRange.count=t}applyMatrix4(e){let t=this.attributes.position;t!==void 0&&(t.applyMatrix4(e),t.needsUpdate=!0);let n=this.attributes.normal;if(n!==void 0){let s=new ke().getNormalMatrix(e);n.applyNormalMatrix(s),n.needsUpdate=!0}let r=this.attributes.tangent;return r!==void 0&&(r.transformDirection(e),r.needsUpdate=!0),this.boundingBox!==null&&this.computeBoundingBox(),this.boundingSphere!==null&&this.computeBoundingSphere(),this}applyQuaternion(e){return cn.makeRotationFromQuaternion(e),this.applyMatrix4(cn),this}rotateX(e){return cn.makeRotationX(e),this.applyMatrix4(cn),this}rotateY(e){return cn.makeRotationY(e),this.applyMatrix4(cn),this}rotateZ(e){return cn.makeRotationZ(e),this.applyMatrix4(cn),this}translate(e,t,n){return cn.makeTranslation(e,t,n),this.applyMatrix4(cn),this}scale(e,t,n){return cn.makeScale(e,t,n),this.applyMatrix4(cn),this}lookAt(e){return ul.lookAt(e),ul.updateMatrix(),this.applyMatrix4(ul.matrix),this}center(){return this.computeBoundingBox(),this.boundingBox.getCenter(er).negate(),this.translate(er.x,er.y,er.z),this}setFromPoints(e){let t=this.getAttribute("position");if(t===void 0){let n=[];for(let r=0,s=e.length;r<s;r++){let a=e[r];n.push(a.x,a.y,a.z||0)}this.setAttribute("position",new nt(n,3))}else{let n=Math.min(e.length,t.count);for(let r=0;r<n;r++){let s=e[r];t.setXYZ(r,s.x,s.y,s.z||0)}e.length>t.count&&console.warn("THREE.BufferGeometry: Buffer size too small for points data. Use .dispose() and create a new geometry."),t.needsUpdate=!0}return this}computeBoundingBox(){this.boundingBox===null&&(this.boundingBox=new oi);let e=this.attributes.position,t=this.morphAttributes.position;if(e&&e.isGLBufferAttribute){console.error("THREE.BufferGeometry.computeBoundingBox(): GLBufferAttribute requires a manual bounding box.",this),this.boundingBox.set(new D(-1/0,-1/0,-1/0),new D(1/0,1/0,1/0));return}if(e!==void 0){if(this.boundingBox.setFromBufferAttribute(e),t)for(let n=0,r=t.length;n<r;n++){let s=t[n];Qt.setFromBufferAttribute(s),this.morphTargetsRelative?(Ct.addVectors(this.boundingBox.min,Qt.min),this.boundingBox.expandByPoint(Ct),Ct.addVectors(this.boundingBox.max,Qt.max),this.boundingBox.expandByPoint(Ct)):(this.boundingBox.expandByPoint(Qt.min),this.boundingBox.expandByPoint(Qt.max))}}else this.boundingBox.makeEmpty();(isNaN(this.boundingBox.min.x)||isNaN(this.boundingBox.min.y)||isNaN(this.boundingBox.min.z))&&console.error('THREE.BufferGeometry.computeBoundingBox(): Computed min/max have NaN values. The "position" attribute is likely to have NaN values.',this)}computeBoundingSphere(){this.boundingSphere===null&&(this.boundingSphere=new li);let e=this.attributes.position,t=this.morphAttributes.position;if(e&&e.isGLBufferAttribute){console.error("THREE.BufferGeometry.computeBoundingSphere(): GLBufferAttribute requires a manual bounding sphere.",this),this.boundingSphere.set(new D,1/0);return}if(e){let n=this.boundingSphere.center;if(Qt.setFromBufferAttribute(e),t)for(let s=0,a=t.length;s<a;s++){let o=t[s];Lr.setFromBufferAttribute(o),this.morphTargetsRelative?(Ct.addVectors(Qt.min,Lr.min),Qt.expandByPoint(Ct),Ct.addVectors(Qt.max,Lr.max),Qt.expandByPoint(Ct)):(Qt.expandByPoint(Lr.min),Qt.expandByPoint(Lr.max))}Qt.getCenter(n);let r=0;for(let s=0,a=e.count;s<a;s++)Ct.fromBufferAttribute(e,s),r=Math.max(r,n.distanceToSquared(Ct));if(t)for(let s=0,a=t.length;s<a;s++){let o=t[s],c=this.morphTargetsRelative;for(let l=0,u=o.count;l<u;l++)Ct.fromBufferAttribute(o,l),c&&(er.fromBufferAttribute(e,l),Ct.add(er)),r=Math.max(r,n.distanceToSquared(Ct))}this.boundingSphere.radius=Math.sqrt(r),isNaN(this.boundingSphere.radius)&&console.error('THREE.BufferGeometry.computeBoundingSphere(): Computed radius is NaN. The "position" attribute is likely to have NaN values.',this)}}computeTangents(){let e=this.index,t=this.attributes;if(e===null||t.position===void 0||t.normal===void 0||t.uv===void 0){console.error("THREE.BufferGeometry: .computeTangents() failed. Missing required attributes (index, position, normal or uv)");return}let n=t.position,r=t.normal,s=t.uv;this.hasAttribute("tangent")===!1&&this.setAttribute("tangent",new Vt(new Float32Array(4*n.count),4));let a=this.getAttribute("tangent"),o=[],c=[];for(let N=0;N<n.count;N++)o[N]=new D,c[N]=new D;let l=new D,u=new D,d=new D,h=new We,p=new We,g=new We,x=new D,m=new D;function f(N,v,b){l.fromBufferAttribute(n,N),u.fromBufferAttribute(n,v),d.fromBufferAttribute(n,b),h.fromBufferAttribute(s,N),p.fromBufferAttribute(s,v),g.fromBufferAttribute(s,b),u.sub(l),d.sub(l),p.sub(h),g.sub(h);let T=1/(p.x*g.y-g.x*p.y);isFinite(T)&&(x.copy(u).multiplyScalar(g.y).addScaledVector(d,-p.y).multiplyScalar(T),m.copy(d).multiplyScalar(p.x).addScaledVector(u,-g.x).multiplyScalar(T),o[N].add(x),o[v].add(x),o[b].add(x),c[N].add(m),c[v].add(m),c[b].add(m))}let S=this.groups;S.length===0&&(S=[{start:0,count:e.count}]);for(let N=0,v=S.length;N<v;++N){let b=S[N],T=b.start,P=b.count;for(let U=T,F=T+P;U<F;U+=3)f(e.getX(U+0),e.getX(U+1),e.getX(U+2))}let M=new D,y=new D,C=new D,A=new D;function I(N){C.fromBufferAttribute(r,N),A.copy(C);let v=o[N];M.copy(v),M.sub(C.multiplyScalar(C.dot(v))).normalize(),y.crossVectors(A,v);let T=y.dot(c[N])<0?-1:1;a.setXYZW(N,M.x,M.y,M.z,T)}for(let N=0,v=S.length;N<v;++N){let b=S[N],T=b.start,P=b.count;for(let U=T,F=T+P;U<F;U+=3)I(e.getX(U+0)),I(e.getX(U+1)),I(e.getX(U+2))}}computeVertexNormals(){let e=this.index,t=this.getAttribute("position");if(t!==void 0){let n=this.getAttribute("normal");if(n===void 0)n=new Vt(new Float32Array(t.count*3),3),this.setAttribute("normal",n);else for(let h=0,p=n.count;h<p;h++)n.setXYZ(h,0,0,0);let r=new D,s=new D,a=new D,o=new D,c=new D,l=new D,u=new D,d=new D;if(e)for(let h=0,p=e.count;h<p;h+=3){let g=e.getX(h+0),x=e.getX(h+1),m=e.getX(h+2);r.fromBufferAttribute(t,g),s.fromBufferAttribute(t,x),a.fromBufferAttribute(t,m),u.subVectors(a,s),d.subVectors(r,s),u.cross(d),o.fromBufferAttribute(n,g),c.fromBufferAttribute(n,x),l.fromBufferAttribute(n,m),o.add(u),c.add(u),l.add(u),n.setXYZ(g,o.x,o.y,o.z),n.setXYZ(x,c.x,c.y,c.z),n.setXYZ(m,l.x,l.y,l.z)}else for(let h=0,p=t.count;h<p;h+=3)r.fromBufferAttribute(t,h+0),s.fromBufferAttribute(t,h+1),a.fromBufferAttribute(t,h+2),u.subVectors(a,s),d.subVectors(r,s),u.cross(d),n.setXYZ(h+0,u.x,u.y,u.z),n.setXYZ(h+1,u.x,u.y,u.z),n.setXYZ(h+2,u.x,u.y,u.z);this.normalizeNormals(),n.needsUpdate=!0}}normalizeNormals(){let e=this.attributes.normal;for(let t=0,n=e.count;t<n;t++)Ct.fromBufferAttribute(e,t),Ct.normalize(),e.setXYZ(t,Ct.x,Ct.y,Ct.z)}toNonIndexed(){function e(o,c){let l=o.array,u=o.itemSize,d=o.normalized,h=new l.constructor(c.length*u),p=0,g=0;for(let x=0,m=c.length;x<m;x++){o.isInterleavedBufferAttribute?p=c[x]*o.data.stride+o.offset:p=c[x]*u;for(let f=0;f<u;f++)h[g++]=l[p++]}return new Vt(h,u,d)}if(this.index===null)return console.warn("THREE.BufferGeometry.toNonIndexed(): BufferGeometry is already non-indexed."),this;let t=new i,n=this.index.array,r=this.attributes;for(let o in r){let c=r[o],l=e(c,n);t.setAttribute(o,l)}let s=this.morphAttributes;for(let o in s){let c=[],l=s[o];for(let u=0,d=l.length;u<d;u++){let h=l[u],p=e(h,n);c.push(p)}t.morphAttributes[o]=c}t.morphTargetsRelative=this.morphTargetsRelative;let a=this.groups;for(let o=0,c=a.length;o<c;o++){let l=a[o];t.addGroup(l.start,l.count,l.materialIndex)}return t}toJSON(){let e={metadata:{version:4.7,type:"BufferGeometry",generator:"BufferGeometry.toJSON"}};if(e.uuid=this.uuid,e.type=this.type,this.name!==""&&(e.name=this.name),Object.keys(this.userData).length>0&&(e.userData=this.userData),this.parameters!==void 0){let c=this.parameters;for(let l in c)c[l]!==void 0&&(e[l]=c[l]);return e}e.data={attributes:{}};let t=this.index;t!==null&&(e.data.index={type:t.array.constructor.name,array:Array.prototype.slice.call(t.array)});let n=this.attributes;for(let c in n){let l=n[c];e.data.attributes[c]=l.toJSON(e.data)}let r={},s=!1;for(let c in this.morphAttributes){let l=this.morphAttributes[c],u=[];for(let d=0,h=l.length;d<h;d++){let p=l[d];u.push(p.toJSON(e.data))}u.length>0&&(r[c]=u,s=!0)}s&&(e.data.morphAttributes=r,e.data.morphTargetsRelative=this.morphTargetsRelative);let a=this.groups;a.length>0&&(e.data.groups=JSON.parse(JSON.stringify(a)));let o=this.boundingSphere;return o!==null&&(e.data.boundingSphere=o.toJSON()),e}clone(){return new this.constructor().copy(this)}copy(e){this.index=null,this.attributes={},this.morphAttributes={},this.groups=[],this.boundingBox=null,this.boundingSphere=null;let t={};this.name=e.name;let n=e.index;n!==null&&this.setIndex(n.clone());let r=e.attributes;for(let l in r){let u=r[l];this.setAttribute(l,u.clone(t))}let s=e.morphAttributes;for(let l in s){let u=[],d=s[l];for(let h=0,p=d.length;h<p;h++)u.push(d[h].clone(t));this.morphAttributes[l]=u}this.morphTargetsRelative=e.morphTargetsRelative;let a=e.groups;for(let l=0,u=a.length;l<u;l++){let d=a[l];this.addGroup(d.start,d.count,d.materialIndex)}let o=e.boundingBox;o!==null&&(this.boundingBox=o.clone());let c=e.boundingSphere;return c!==null&&(this.boundingSphere=c.clone()),this.drawRange.start=e.drawRange.start,this.drawRange.count=e.drawRange.count,this.userData=e.userData,this}dispose(){this.dispatchEvent({type:"dispose"})}},Qc=new ht,bi=new fr,zs=new li,ed=new D,ks=new D,Hs=new D,Vs=new D,hl=new D,Gs=new D,td=new D,Ws=new D,dt=class extends Mt{constructor(e=new ft,t=new Wt){super(),this.isMesh=!0,this.type="Mesh",this.geometry=e,this.material=t,this.morphTargetDictionary=void 0,this.morphTargetInfluences=void 0,this.count=1,this.updateMorphTargets()}copy(e,t){return super.copy(e,t),e.morphTargetInfluences!==void 0&&(this.morphTargetInfluences=e.morphTargetInfluences.slice()),e.morphTargetDictionary!==void 0&&(this.morphTargetDictionary=Object.assign({},e.morphTargetDictionary)),this.material=Array.isArray(e.material)?e.material.slice():e.material,this.geometry=e.geometry,this}updateMorphTargets(){let t=this.geometry.morphAttributes,n=Object.keys(t);if(n.length>0){let r=t[n[0]];if(r!==void 0){this.morphTargetInfluences=[],this.morphTargetDictionary={};for(let s=0,a=r.length;s<a;s++){let o=r[s].name||String(s);this.morphTargetInfluences.push(0),this.morphTargetDictionary[o]=s}}}}getVertexPosition(e,t){let n=this.geometry,r=n.attributes.position,s=n.morphAttributes.position,a=n.morphTargetsRelative;t.fromBufferAttribute(r,e);let o=this.morphTargetInfluences;if(s&&o){Gs.set(0,0,0);for(let c=0,l=s.length;c<l;c++){let u=o[c],d=s[c];u!==0&&(hl.fromBufferAttribute(d,e),a?Gs.addScaledVector(hl,u):Gs.addScaledVector(hl.sub(t),u))}t.add(Gs)}return t}raycast(e,t){let n=this.geometry,r=this.material,s=this.matrixWorld;r!==void 0&&(n.boundingSphere===null&&n.computeBoundingSphere(),zs.copy(n.boundingSphere),zs.applyMatrix4(s),bi.copy(e.ray).recast(e.near),!(zs.containsPoint(bi.origin)===!1&&(bi.intersectSphere(zs,ed)===null||bi.origin.distanceToSquared(ed)>(e.far-e.near)**2))&&(Qc.copy(s).invert(),bi.copy(e.ray).applyMatrix4(Qc),!(n.boundingBox!==null&&bi.intersectsBox(n.boundingBox)===!1)&&this._computeIntersections(e,t,bi)))}_computeIntersections(e,t,n){let r,s=this.geometry,a=this.material,o=s.index,c=s.attributes.position,l=s.attributes.uv,u=s.attributes.uv1,d=s.attributes.normal,h=s.groups,p=s.drawRange;if(o!==null)if(Array.isArray(a))for(let g=0,x=h.length;g<x;g++){let m=h[g],f=a[m.materialIndex],S=Math.max(m.start,p.start),M=Math.min(o.count,Math.min(m.start+m.count,p.start+p.count));for(let y=S,C=M;y<C;y+=3){let A=o.getX(y),I=o.getX(y+1),N=o.getX(y+2);r=Xs(this,f,e,n,l,u,d,A,I,N),r&&(r.faceIndex=Math.floor(y/3),r.face.materialIndex=m.materialIndex,t.push(r))}}else{let g=Math.max(0,p.start),x=Math.min(o.count,p.start+p.count);for(let m=g,f=x;m<f;m+=3){let S=o.getX(m),M=o.getX(m+1),y=o.getX(m+2);r=Xs(this,a,e,n,l,u,d,S,M,y),r&&(r.faceIndex=Math.floor(m/3),t.push(r))}}else if(c!==void 0)if(Array.isArray(a))for(let g=0,x=h.length;g<x;g++){let m=h[g],f=a[m.materialIndex],S=Math.max(m.start,p.start),M=Math.min(c.count,Math.min(m.start+m.count,p.start+p.count));for(let y=S,C=M;y<C;y+=3){let A=y,I=y+1,N=y+2;r=Xs(this,f,e,n,l,u,d,A,I,N),r&&(r.faceIndex=Math.floor(y/3),r.face.materialIndex=m.materialIndex,t.push(r))}}else{let g=Math.max(0,p.start),x=Math.min(c.count,p.start+p.count);for(let m=g,f=x;m<f;m+=3){let S=m,M=m+1,y=m+2;r=Xs(this,a,e,n,l,u,d,S,M,y),r&&(r.faceIndex=Math.floor(m/3),t.push(r))}}}};function sf(i,e,t,n,r,s,a,o){let c;if(e.side===zt?c=n.intersectTriangle(a,s,r,!0,o):c=n.intersectTriangle(r,s,a,e.side===Gn,o),c===null)return null;Ws.copy(o),Ws.applyMatrix4(i.matrixWorld);let l=t.ray.origin.distanceTo(Ws);return l<t.near||l>t.far?null:{distance:l,point:Ws.clone(),object:i}}function Xs(i,e,t,n,r,s,a,o,c,l){i.getVertexPosition(o,ks),i.getVertexPosition(c,Hs),i.getVertexPosition(l,Vs);let u=sf(i,e,t,n,ks,Hs,Vs,td);if(u){let d=new D;Cn.getBarycoord(td,ks,Hs,Vs,d),r&&(u.uv=Cn.getInterpolatedAttribute(r,o,c,l,d,new We)),s&&(u.uv1=Cn.getInterpolatedAttribute(s,o,c,l,d,new We)),a&&(u.normal=Cn.getInterpolatedAttribute(a,o,c,l,d,new D),u.normal.dot(n.direction)>0&&u.normal.multiplyScalar(-1));let h={a:o,b:c,c:l,normal:new D,materialIndex:0};Cn.getNormal(ks,Hs,Vs,h.normal),u.face=h,u.barycoord=d}return u}var Mn=class i extends ft{constructor(e=1,t=1,n=1,r=1,s=1,a=1){super(),this.type="BoxGeometry",this.parameters={width:e,height:t,depth:n,widthSegments:r,heightSegments:s,depthSegments:a};let o=this;r=Math.floor(r),s=Math.floor(s),a=Math.floor(a);let c=[],l=[],u=[],d=[],h=0,p=0;g("z","y","x",-1,-1,n,t,e,a,s,0),g("z","y","x",1,-1,n,t,-e,a,s,1),g("x","z","y",1,1,e,n,t,r,a,2),g("x","z","y",1,-1,e,n,-t,r,a,3),g("x","y","z",1,-1,e,t,n,r,s,4),g("x","y","z",-1,-1,e,t,-n,r,s,5),this.setIndex(c),this.setAttribute("position",new nt(l,3)),this.setAttribute("normal",new nt(u,3)),this.setAttribute("uv",new nt(d,2));function g(x,m,f,S,M,y,C,A,I,N,v){let b=y/I,T=C/N,P=y/2,U=C/2,F=A/2,k=I+1,G=N+1,K=0,W=0,se=new D;for(let de=0;de<G;de++){let Ae=de*T-U;for(let fe=0;fe<k;fe++){let Oe=fe*b-P;se[x]=Oe*S,se[m]=Ae*M,se[f]=F,l.push(se.x,se.y,se.z),se[x]=0,se[m]=0,se[f]=A>0?1:-1,u.push(se.x,se.y,se.z),d.push(fe/I),d.push(1-de/N),K+=1}}for(let de=0;de<N;de++)for(let Ae=0;Ae<I;Ae++){let fe=h+Ae+k*de,Oe=h+Ae+k*(de+1),$e=h+(Ae+1)+k*(de+1),Pe=h+(Ae+1)+k*de;c.push(fe,Oe,Pe),c.push(Oe,$e,Pe),W+=6}o.addGroup(p,W,v),p+=W,h+=K}}copy(e){return super.copy(e),this.parameters=Object.assign({},e.parameters),this}static fromJSON(e){return new i(e.width,e.height,e.depth,e.widthSegments,e.heightSegments,e.depthSegments)}};function Pi(i){let e={};for(let t in i){e[t]={};for(let n in i[t]){let r=i[t][n];r&&(r.isColor||r.isMatrix3||r.isMatrix4||r.isVector2||r.isVector3||r.isVector4||r.isTexture||r.isQuaternion)?r.isRenderTargetTexture?(console.warn("UniformsUtils: Textures of render targets cannot be cloned via cloneUniforms() or mergeUniforms()."),e[t][n]=null):e[t][n]=r.clone():Array.isArray(r)?e[t][n]=r.slice():e[t][n]=r}}return e}function Ft(i){let e={};for(let t=0;t<i.length;t++){let n=Pi(i[t]);for(let r in n)e[r]=n[r]}return e}function af(i){let e=[];for(let t=0;t<i.length;t++)e.push(i[t].clone());return e}function ql(i){let e=i.getRenderTarget();return e===null?i.outputColorSpace:e.isXRRenderTarget===!0?e.texture.colorSpace:Ke.workingColorSpace}var su={clone:Pi,merge:Ft},of=`void main() {
	gl_Position = projectionMatrix * modelViewMatrix * vec4( position, 1.0 );
}`,lf=`void main() {
	gl_FragColor = vec4( 1.0, 0.0, 0.0, 1.0 );
}`,tn=class extends wn{constructor(e){super(),this.isShaderMaterial=!0,this.type="ShaderMaterial",this.defines={},this.uniforms={},this.uniformsGroups=[],this.vertexShader=of,this.fragmentShader=lf,this.linewidth=1,this.wireframe=!1,this.wireframeLinewidth=1,this.fog=!1,this.lights=!1,this.clipping=!1,this.forceSinglePass=!0,this.extensions={clipCullDistance:!1,multiDraw:!1},this.defaultAttributeValues={color:[1,1,1],uv:[0,0],uv1:[0,0]},this.index0AttributeName=void 0,this.uniformsNeedUpdate=!1,this.glslVersion=null,e!==void 0&&this.setValues(e)}copy(e){return super.copy(e),this.fragmentShader=e.fragmentShader,this.vertexShader=e.vertexShader,this.uniforms=Pi(e.uniforms),this.uniformsGroups=af(e.uniformsGroups),this.defines=Object.assign({},e.defines),this.wireframe=e.wireframe,this.wireframeLinewidth=e.wireframeLinewidth,this.fog=e.fog,this.lights=e.lights,this.clipping=e.clipping,this.extensions=Object.assign({},e.extensions),this.glslVersion=e.glslVersion,this}toJSON(e){let t=super.toJSON(e);t.glslVersion=this.glslVersion,t.uniforms={};for(let r in this.uniforms){let a=this.uniforms[r].value;a&&a.isTexture?t.uniforms[r]={type:"t",value:a.toJSON(e).uuid}:a&&a.isColor?t.uniforms[r]={type:"c",value:a.getHex()}:a&&a.isVector2?t.uniforms[r]={type:"v2",value:a.toArray()}:a&&a.isVector3?t.uniforms[r]={type:"v3",value:a.toArray()}:a&&a.isVector4?t.uniforms[r]={type:"v4",value:a.toArray()}:a&&a.isMatrix3?t.uniforms[r]={type:"m3",value:a.toArray()}:a&&a.isMatrix4?t.uniforms[r]={type:"m4",value:a.toArray()}:t.uniforms[r]={value:a}}Object.keys(this.defines).length>0&&(t.defines=this.defines),t.vertexShader=this.vertexShader,t.fragmentShader=this.fragmentShader,t.lights=this.lights,t.clipping=this.clipping;let n={};for(let r in this.extensions)this.extensions[r]===!0&&(n[r]=!0);return Object.keys(n).length>0&&(t.extensions=n),t}},Yr=class extends Mt{constructor(){super(),this.isCamera=!0,this.type="Camera",this.matrixWorldInverse=new ht,this.projectionMatrix=new ht,this.projectionMatrixInverse=new ht,this.coordinateSystem=vn,this._reversedDepth=!1}get reversedDepth(){return this._reversedDepth}copy(e,t){return super.copy(e,t),this.matrixWorldInverse.copy(e.matrixWorldInverse),this.projectionMatrix.copy(e.projectionMatrix),this.projectionMatrixInverse.copy(e.projectionMatrixInverse),this.coordinateSystem=e.coordinateSystem,this}getWorldDirection(e){return super.getWorldDirection(e).negate()}updateMatrixWorld(e){super.updateMatrixWorld(e),this.matrixWorldInverse.copy(this.matrixWorld).invert()}updateWorldMatrix(e,t){super.updateWorldMatrix(e,t),this.matrixWorldInverse.copy(this.matrixWorld).invert()}clone(){return new this.constructor().copy(this)}},ri=new D,nd=new We,id=new We,Dt=class extends Yr{constructor(e=50,t=1,n=.1,r=2e3){super(),this.isPerspectiveCamera=!0,this.type="PerspectiveCamera",this.fov=e,this.zoom=1,this.near=n,this.far=r,this.focus=10,this.aspect=t,this.view=null,this.filmGauge=35,this.filmOffset=0,this.updateProjectionMatrix()}copy(e,t){return super.copy(e,t),this.fov=e.fov,this.zoom=e.zoom,this.near=e.near,this.far=e.far,this.focus=e.focus,this.aspect=e.aspect,this.view=e.view===null?null:Object.assign({},e.view),this.filmGauge=e.filmGauge,this.filmOffset=e.filmOffset,this}setFocalLength(e){let t=.5*this.getFilmHeight()/e;this.fov=dr*2*Math.atan(t),this.updateProjectionMatrix()}getFocalLength(){let e=Math.tan(or*.5*this.fov);return .5*this.getFilmHeight()/e}getEffectiveFOV(){return dr*2*Math.atan(Math.tan(or*.5*this.fov)/this.zoom)}getFilmWidth(){return this.filmGauge*Math.min(this.aspect,1)}getFilmHeight(){return this.filmGauge/Math.max(this.aspect,1)}getViewBounds(e,t,n){ri.set(-1,-1,.5).applyMatrix4(this.projectionMatrixInverse),t.set(ri.x,ri.y).multiplyScalar(-e/ri.z),ri.set(1,1,.5).applyMatrix4(this.projectionMatrixInverse),n.set(ri.x,ri.y).multiplyScalar(-e/ri.z)}getViewSize(e,t){return this.getViewBounds(e,nd,id),t.subVectors(id,nd)}setViewOffset(e,t,n,r,s,a){this.aspect=e/t,this.view===null&&(this.view={enabled:!0,fullWidth:1,fullHeight:1,offsetX:0,offsetY:0,width:1,height:1}),this.view.enabled=!0,this.view.fullWidth=e,this.view.fullHeight=t,this.view.offsetX=n,this.view.offsetY=r,this.view.width=s,this.view.height=a,this.updateProjectionMatrix()}clearViewOffset(){this.view!==null&&(this.view.enabled=!1),this.updateProjectionMatrix()}updateProjectionMatrix(){let e=this.near,t=e*Math.tan(or*.5*this.fov)/this.zoom,n=2*t,r=this.aspect*n,s=-.5*r,a=this.view;if(this.view!==null&&this.view.enabled){let c=a.fullWidth,l=a.fullHeight;s+=a.offsetX*r/c,t-=a.offsetY*n/l,r*=a.width/c,n*=a.height/l}let o=this.filmOffset;o!==0&&(s+=e*o/this.getFilmWidth()),this.projectionMatrix.makePerspective(s,s+r,t,t-n,e,this.far,this.coordinateSystem,this.reversedDepth),this.projectionMatrixInverse.copy(this.projectionMatrix).invert()}toJSON(e){let t=super.toJSON(e);return t.object.fov=this.fov,t.object.zoom=this.zoom,t.object.near=this.near,t.object.far=this.far,t.object.focus=this.focus,t.object.aspect=this.aspect,this.view!==null&&(t.object.view=Object.assign({},this.view)),t.object.filmGauge=this.filmGauge,t.object.filmOffset=this.filmOffset,t}},tr=-90,nr=1,ma=class extends Mt{constructor(e,t,n){super(),this.type="CubeCamera",this.renderTarget=n,this.coordinateSystem=null,this.activeMipmapLevel=0;let r=new Dt(tr,nr,e,t);r.layers=this.layers,this.add(r);let s=new Dt(tr,nr,e,t);s.layers=this.layers,this.add(s);let a=new Dt(tr,nr,e,t);a.layers=this.layers,this.add(a);let o=new Dt(tr,nr,e,t);o.layers=this.layers,this.add(o);let c=new Dt(tr,nr,e,t);c.layers=this.layers,this.add(c);let l=new Dt(tr,nr,e,t);l.layers=this.layers,this.add(l)}updateCoordinateSystem(){let e=this.coordinateSystem,t=this.children.concat(),[n,r,s,a,o,c]=t;for(let l of t)this.remove(l);if(e===vn)n.up.set(0,1,0),n.lookAt(1,0,0),r.up.set(0,1,0),r.lookAt(-1,0,0),s.up.set(0,0,-1),s.lookAt(0,1,0),a.up.set(0,0,1),a.lookAt(0,-1,0),o.up.set(0,1,0),o.lookAt(0,0,1),c.up.set(0,1,0),c.lookAt(0,0,-1);else if(e===Vr)n.up.set(0,-1,0),n.lookAt(-1,0,0),r.up.set(0,-1,0),r.lookAt(1,0,0),s.up.set(0,0,1),s.lookAt(0,1,0),a.up.set(0,0,-1),a.lookAt(0,-1,0),o.up.set(0,-1,0),o.lookAt(0,0,1),c.up.set(0,-1,0),c.lookAt(0,0,-1);else throw new Error("THREE.CubeCamera.updateCoordinateSystem(): Invalid coordinate system: "+e);for(let l of t)this.add(l),l.updateMatrixWorld()}update(e,t){this.parent===null&&this.updateMatrixWorld();let{renderTarget:n,activeMipmapLevel:r}=this;this.coordinateSystem!==e.coordinateSystem&&(this.coordinateSystem=e.coordinateSystem,this.updateCoordinateSystem());let[s,a,o,c,l,u]=this.children,d=e.getRenderTarget(),h=e.getActiveCubeFace(),p=e.getActiveMipmapLevel(),g=e.xr.enabled;e.xr.enabled=!1;let x=n.texture.generateMipmaps;n.texture.generateMipmaps=!1,e.setRenderTarget(n,0,r),e.render(t,s),e.setRenderTarget(n,1,r),e.render(t,a),e.setRenderTarget(n,2,r),e.render(t,o),e.setRenderTarget(n,3,r),e.render(t,c),e.setRenderTarget(n,4,r),e.render(t,l),n.texture.generateMipmaps=x,e.setRenderTarget(n,5,r),e.render(t,u),e.setRenderTarget(d,h,p),e.xr.enabled=g,n.texture.needsPMREMUpdate=!0}},Zr=class extends Lt{constructor(e=[],t=Ri,n,r,s,a,o,c,l,u){super(e,t,n,r,s,a,o,c,l,u),this.isCubeTexture=!0,this.flipY=!1}get images(){return this.image}set images(e){this.image=e}},ga=class extends Rn{constructor(e=1,t={}){super(e,e,t),this.isWebGLCubeRenderTarget=!0;let n={width:e,height:e,depth:1},r=[n,n,n,n,n,n];this.texture=new Zr(r),this._setTextureOptions(t),this.texture.isRenderTargetTexture=!0}fromEquirectangularTexture(e,t){this.texture.type=t.type,this.texture.colorSpace=t.colorSpace,this.texture.generateMipmaps=t.generateMipmaps,this.texture.minFilter=t.minFilter,this.texture.magFilter=t.magFilter;let n={uniforms:{tEquirect:{value:null}},vertexShader:`

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
			`},r=new Mn(5,5,5),s=new tn({name:"CubemapFromEquirect",uniforms:Pi(n.uniforms),vertexShader:n.vertexShader,fragmentShader:n.fragmentShader,side:zt,blending:$n});s.uniforms.tEquirect.value=t;let a=new dt(r,s),o=t.minFilter;return t.minFilter===fi&&(t.minFilter=bn),new ma(1,10,this).update(e,a),t.minFilter=o,a.geometry.dispose(),a.material.dispose(),this}clear(e,t=!0,n=!0,r=!0){let s=e.getRenderTarget();for(let a=0;a<6;a++)e.setRenderTarget(this,a),e.clear(t,n,r);e.setRenderTarget(s)}},Bt=class extends Mt{constructor(){super(),this.isGroup=!0,this.type="Group"}},cf={type:"move"},pr=class{constructor(){this._targetRay=null,this._grip=null,this._hand=null}getHandSpace(){return this._hand===null&&(this._hand=new Bt,this._hand.matrixAutoUpdate=!1,this._hand.visible=!1,this._hand.joints={},this._hand.inputState={pinching:!1}),this._hand}getTargetRaySpace(){return this._targetRay===null&&(this._targetRay=new Bt,this._targetRay.matrixAutoUpdate=!1,this._targetRay.visible=!1,this._targetRay.hasLinearVelocity=!1,this._targetRay.linearVelocity=new D,this._targetRay.hasAngularVelocity=!1,this._targetRay.angularVelocity=new D),this._targetRay}getGripSpace(){return this._grip===null&&(this._grip=new Bt,this._grip.matrixAutoUpdate=!1,this._grip.visible=!1,this._grip.hasLinearVelocity=!1,this._grip.linearVelocity=new D,this._grip.hasAngularVelocity=!1,this._grip.angularVelocity=new D),this._grip}dispatchEvent(e){return this._targetRay!==null&&this._targetRay.dispatchEvent(e),this._grip!==null&&this._grip.dispatchEvent(e),this._hand!==null&&this._hand.dispatchEvent(e),this}connect(e){if(e&&e.hand){let t=this._hand;if(t)for(let n of e.hand.values())this._getHandJoint(t,n)}return this.dispatchEvent({type:"connected",data:e}),this}disconnect(e){return this.dispatchEvent({type:"disconnected",data:e}),this._targetRay!==null&&(this._targetRay.visible=!1),this._grip!==null&&(this._grip.visible=!1),this._hand!==null&&(this._hand.visible=!1),this}update(e,t,n){let r=null,s=null,a=null,o=this._targetRay,c=this._grip,l=this._hand;if(e&&t.session.visibilityState!=="visible-blurred"){if(l&&e.hand){a=!0;for(let x of e.hand.values()){let m=t.getJointPose(x,n),f=this._getHandJoint(l,x);m!==null&&(f.matrix.fromArray(m.transform.matrix),f.matrix.decompose(f.position,f.rotation,f.scale),f.matrixWorldNeedsUpdate=!0,f.jointRadius=m.radius),f.visible=m!==null}let u=l.joints["index-finger-tip"],d=l.joints["thumb-tip"],h=u.position.distanceTo(d.position),p=.02,g=.005;l.inputState.pinching&&h>p+g?(l.inputState.pinching=!1,this.dispatchEvent({type:"pinchend",handedness:e.handedness,target:this})):!l.inputState.pinching&&h<=p-g&&(l.inputState.pinching=!0,this.dispatchEvent({type:"pinchstart",handedness:e.handedness,target:this}))}else c!==null&&e.gripSpace&&(s=t.getPose(e.gripSpace,n),s!==null&&(c.matrix.fromArray(s.transform.matrix),c.matrix.decompose(c.position,c.rotation,c.scale),c.matrixWorldNeedsUpdate=!0,s.linearVelocity?(c.hasLinearVelocity=!0,c.linearVelocity.copy(s.linearVelocity)):c.hasLinearVelocity=!1,s.angularVelocity?(c.hasAngularVelocity=!0,c.angularVelocity.copy(s.angularVelocity)):c.hasAngularVelocity=!1));o!==null&&(r=t.getPose(e.targetRaySpace,n),r===null&&s!==null&&(r=s),r!==null&&(o.matrix.fromArray(r.transform.matrix),o.matrix.decompose(o.position,o.rotation,o.scale),o.matrixWorldNeedsUpdate=!0,r.linearVelocity?(o.hasLinearVelocity=!0,o.linearVelocity.copy(r.linearVelocity)):o.hasLinearVelocity=!1,r.angularVelocity?(o.hasAngularVelocity=!0,o.angularVelocity.copy(r.angularVelocity)):o.hasAngularVelocity=!1,this.dispatchEvent(cf)))}return o!==null&&(o.visible=r!==null),c!==null&&(c.visible=s!==null),l!==null&&(l.visible=a!==null),this}_getHandJoint(e,t){if(e.joints[t.jointName]===void 0){let n=new Bt;n.matrixAutoUpdate=!1,n.visible=!1,e.joints[t.jointName]=n,e.add(n)}return e.joints[t.jointName]}};var Jr=class extends Mt{constructor(){super(),this.isScene=!0,this.type="Scene",this.background=null,this.environment=null,this.fog=null,this.backgroundBlurriness=0,this.backgroundIntensity=1,this.backgroundRotation=new en,this.environmentIntensity=1,this.environmentRotation=new en,this.overrideMaterial=null,typeof __THREE_DEVTOOLS__<"u"&&__THREE_DEVTOOLS__.dispatchEvent(new CustomEvent("observe",{detail:this}))}copy(e,t){return super.copy(e,t),e.background!==null&&(this.background=e.background.clone()),e.environment!==null&&(this.environment=e.environment.clone()),e.fog!==null&&(this.fog=e.fog.clone()),this.backgroundBlurriness=e.backgroundBlurriness,this.backgroundIntensity=e.backgroundIntensity,this.backgroundRotation.copy(e.backgroundRotation),this.environmentIntensity=e.environmentIntensity,this.environmentRotation.copy(e.environmentRotation),e.overrideMaterial!==null&&(this.overrideMaterial=e.overrideMaterial.clone()),this.matrixAutoUpdate=e.matrixAutoUpdate,this}toJSON(e){let t=super.toJSON(e);return this.fog!==null&&(t.object.fog=this.fog.toJSON()),this.backgroundBlurriness>0&&(t.object.backgroundBlurriness=this.backgroundBlurriness),this.backgroundIntensity!==1&&(t.object.backgroundIntensity=this.backgroundIntensity),t.object.backgroundRotation=this.backgroundRotation.toArray(),this.environmentIntensity!==1&&(t.object.environmentIntensity=this.environmentIntensity),t.object.environmentRotation=this.environmentRotation.toArray(),t}},xa=class{constructor(e,t){this.isInterleavedBuffer=!0,this.array=e,this.stride=t,this.count=e!==void 0?e.length/t:0,this.usage=ua,this.updateRanges=[],this.version=0,this.uuid=Hn()}onUploadCallback(){}set needsUpdate(e){e===!0&&this.version++}setUsage(e){return this.usage=e,this}addUpdateRange(e,t){this.updateRanges.push({start:e,count:t})}clearUpdateRanges(){this.updateRanges.length=0}copy(e){return this.array=new e.array.constructor(e.array),this.count=e.count,this.stride=e.stride,this.usage=e.usage,this}copyAt(e,t,n){e*=this.stride,n*=t.stride;for(let r=0,s=this.stride;r<s;r++)this.array[e+r]=t.array[n+r];return this}set(e,t=0){return this.array.set(e,t),this}clone(e){e.arrayBuffers===void 0&&(e.arrayBuffers={}),this.array.buffer._uuid===void 0&&(this.array.buffer._uuid=Hn()),e.arrayBuffers[this.array.buffer._uuid]===void 0&&(e.arrayBuffers[this.array.buffer._uuid]=this.array.slice(0).buffer);let t=new this.array.constructor(e.arrayBuffers[this.array.buffer._uuid]),n=new this.constructor(t,this.stride);return n.setUsage(this.usage),n}onUpload(e){return this.onUploadCallback=e,this}toJSON(e){return e.arrayBuffers===void 0&&(e.arrayBuffers={}),this.array.buffer._uuid===void 0&&(this.array.buffer._uuid=Hn()),e.arrayBuffers[this.array.buffer._uuid]===void 0&&(e.arrayBuffers[this.array.buffer._uuid]=Array.from(new Uint32Array(this.array.buffer))),{uuid:this.uuid,buffer:this.array.buffer._uuid,type:this.array.constructor.name,stride:this.stride}}},Ot=new D,Kr=class i{constructor(e,t,n,r=!1){this.isInterleavedBufferAttribute=!0,this.name="",this.data=e,this.itemSize=t,this.offset=n,this.normalized=r}get count(){return this.data.count}get array(){return this.data.array}set needsUpdate(e){this.data.needsUpdate=e}applyMatrix4(e){for(let t=0,n=this.data.count;t<n;t++)Ot.fromBufferAttribute(this,t),Ot.applyMatrix4(e),this.setXYZ(t,Ot.x,Ot.y,Ot.z);return this}applyNormalMatrix(e){for(let t=0,n=this.count;t<n;t++)Ot.fromBufferAttribute(this,t),Ot.applyNormalMatrix(e),this.setXYZ(t,Ot.x,Ot.y,Ot.z);return this}transformDirection(e){for(let t=0,n=this.count;t<n;t++)Ot.fromBufferAttribute(this,t),Ot.transformDirection(e),this.setXYZ(t,Ot.x,Ot.y,Ot.z);return this}getComponent(e,t){let n=this.array[e*this.data.stride+this.offset+t];return this.normalized&&(n=yn(n,this.array)),n}setComponent(e,t,n){return this.normalized&&(n=et(n,this.array)),this.data.array[e*this.data.stride+this.offset+t]=n,this}setX(e,t){return this.normalized&&(t=et(t,this.array)),this.data.array[e*this.data.stride+this.offset]=t,this}setY(e,t){return this.normalized&&(t=et(t,this.array)),this.data.array[e*this.data.stride+this.offset+1]=t,this}setZ(e,t){return this.normalized&&(t=et(t,this.array)),this.data.array[e*this.data.stride+this.offset+2]=t,this}setW(e,t){return this.normalized&&(t=et(t,this.array)),this.data.array[e*this.data.stride+this.offset+3]=t,this}getX(e){let t=this.data.array[e*this.data.stride+this.offset];return this.normalized&&(t=yn(t,this.array)),t}getY(e){let t=this.data.array[e*this.data.stride+this.offset+1];return this.normalized&&(t=yn(t,this.array)),t}getZ(e){let t=this.data.array[e*this.data.stride+this.offset+2];return this.normalized&&(t=yn(t,this.array)),t}getW(e){let t=this.data.array[e*this.data.stride+this.offset+3];return this.normalized&&(t=yn(t,this.array)),t}setXY(e,t,n){return e=e*this.data.stride+this.offset,this.normalized&&(t=et(t,this.array),n=et(n,this.array)),this.data.array[e+0]=t,this.data.array[e+1]=n,this}setXYZ(e,t,n,r){return e=e*this.data.stride+this.offset,this.normalized&&(t=et(t,this.array),n=et(n,this.array),r=et(r,this.array)),this.data.array[e+0]=t,this.data.array[e+1]=n,this.data.array[e+2]=r,this}setXYZW(e,t,n,r,s){return e=e*this.data.stride+this.offset,this.normalized&&(t=et(t,this.array),n=et(n,this.array),r=et(r,this.array),s=et(s,this.array)),this.data.array[e+0]=t,this.data.array[e+1]=n,this.data.array[e+2]=r,this.data.array[e+3]=s,this}clone(e){if(e===void 0){console.log("THREE.InterleavedBufferAttribute.clone(): Cloning an interleaved buffer attribute will de-interleave buffer data.");let t=[];for(let n=0;n<this.count;n++){let r=n*this.data.stride+this.offset;for(let s=0;s<this.itemSize;s++)t.push(this.data.array[r+s])}return new Vt(new this.array.constructor(t),this.itemSize,this.normalized)}else return e.interleavedBuffers===void 0&&(e.interleavedBuffers={}),e.interleavedBuffers[this.data.uuid]===void 0&&(e.interleavedBuffers[this.data.uuid]=this.data.clone(e)),new i(e.interleavedBuffers[this.data.uuid],this.itemSize,this.offset,this.normalized)}toJSON(e){if(e===void 0){console.log("THREE.InterleavedBufferAttribute.toJSON(): Serializing an interleaved buffer attribute will de-interleave buffer data.");let t=[];for(let n=0;n<this.count;n++){let r=n*this.data.stride+this.offset;for(let s=0;s<this.itemSize;s++)t.push(this.data.array[r+s])}return{itemSize:this.itemSize,type:this.array.constructor.name,array:t,normalized:this.normalized}}else return e.interleavedBuffers===void 0&&(e.interleavedBuffers={}),e.interleavedBuffers[this.data.uuid]===void 0&&(e.interleavedBuffers[this.data.uuid]=this.data.toJSON(e)),{isInterleavedBufferAttribute:!0,itemSize:this.itemSize,data:this.data.uuid,offset:this.offset,normalized:this.normalized}}},mr=class extends wn{constructor(e){super(),this.isSpriteMaterial=!0,this.type="SpriteMaterial",this.color=new Be(16777215),this.map=null,this.alphaMap=null,this.rotation=0,this.sizeAttenuation=!0,this.transparent=!0,this.fog=!0,this.setValues(e)}copy(e){return super.copy(e),this.color.copy(e.color),this.map=e.map,this.alphaMap=e.alphaMap,this.rotation=e.rotation,this.sizeAttenuation=e.sizeAttenuation,this.fog=e.fog,this}},ir,Fr=new D,rr=new D,sr=new D,ar=new We,Ur=new We,au=new ht,$s=new D,Or=new D,qs=new D,rd=new We,fl=new We,sd=new We,jr=class extends Mt{constructor(e=new mr){if(super(),this.isSprite=!0,this.type="Sprite",ir===void 0){ir=new ft;let t=new Float32Array([-.5,-.5,0,0,0,.5,-.5,0,1,0,.5,.5,0,1,1,-.5,.5,0,0,1]),n=new xa(t,5);ir.setIndex([0,1,2,0,2,3]),ir.setAttribute("position",new Kr(n,3,0,!1)),ir.setAttribute("uv",new Kr(n,2,3,!1))}this.geometry=ir,this.material=e,this.center=new We(.5,.5),this.count=1}raycast(e,t){e.camera===null&&console.error('THREE.Sprite: "Raycaster.camera" needs to be set in order to raycast against sprites.'),rr.setFromMatrixScale(this.matrixWorld),au.copy(e.camera.matrixWorld),this.modelViewMatrix.multiplyMatrices(e.camera.matrixWorldInverse,this.matrixWorld),sr.setFromMatrixPosition(this.modelViewMatrix),e.camera.isPerspectiveCamera&&this.material.sizeAttenuation===!1&&rr.multiplyScalar(-sr.z);let n=this.material.rotation,r,s;n!==0&&(s=Math.cos(n),r=Math.sin(n));let a=this.center;Ys($s.set(-.5,-.5,0),sr,a,rr,r,s),Ys(Or.set(.5,-.5,0),sr,a,rr,r,s),Ys(qs.set(.5,.5,0),sr,a,rr,r,s),rd.set(0,0),fl.set(1,0),sd.set(1,1);let o=e.ray.intersectTriangle($s,Or,qs,!1,Fr);if(o===null&&(Ys(Or.set(-.5,.5,0),sr,a,rr,r,s),fl.set(0,1),o=e.ray.intersectTriangle($s,qs,Or,!1,Fr),o===null))return;let c=e.ray.origin.distanceTo(Fr);c<e.near||c>e.far||t.push({distance:c,point:Fr.clone(),uv:Cn.getInterpolation(Fr,$s,Or,qs,rd,fl,sd,new We),face:null,object:this})}copy(e,t){return super.copy(e,t),e.center!==void 0&&this.center.copy(e.center),this.material=e.material,this}};function Ys(i,e,t,n,r,s){ar.subVectors(i,t).addScalar(.5).multiply(n),r!==void 0?(Ur.x=s*ar.x-r*ar.y,Ur.y=r*ar.x+s*ar.y):Ur.copy(ar),i.copy(e),i.x+=Ur.x,i.y+=Ur.y,i.applyMatrix4(au)}var pl=new D,df=new D,uf=new ke,An=class{constructor(e=new D(1,0,0),t=0){this.isPlane=!0,this.normal=e,this.constant=t}set(e,t){return this.normal.copy(e),this.constant=t,this}setComponents(e,t,n,r){return this.normal.set(e,t,n),this.constant=r,this}setFromNormalAndCoplanarPoint(e,t){return this.normal.copy(e),this.constant=-t.dot(this.normal),this}setFromCoplanarPoints(e,t,n){let r=pl.subVectors(n,t).cross(df.subVectors(e,t)).normalize();return this.setFromNormalAndCoplanarPoint(r,e),this}copy(e){return this.normal.copy(e.normal),this.constant=e.constant,this}normalize(){let e=1/this.normal.length();return this.normal.multiplyScalar(e),this.constant*=e,this}negate(){return this.constant*=-1,this.normal.negate(),this}distanceToPoint(e){return this.normal.dot(e)+this.constant}distanceToSphere(e){return this.distanceToPoint(e.center)-e.radius}projectPoint(e,t){return t.copy(e).addScaledVector(this.normal,-this.distanceToPoint(e))}intersectLine(e,t){let n=e.delta(pl),r=this.normal.dot(n);if(r===0)return this.distanceToPoint(e.start)===0?t.copy(e.start):null;let s=-(e.start.dot(this.normal)+this.constant)/r;return s<0||s>1?null:t.copy(e.start).addScaledVector(n,s)}intersectsLine(e){let t=this.distanceToPoint(e.start),n=this.distanceToPoint(e.end);return t<0&&n>0||n<0&&t>0}intersectsBox(e){return e.intersectsPlane(this)}intersectsSphere(e){return e.intersectsPlane(this)}coplanarPoint(e){return e.copy(this.normal).multiplyScalar(-this.constant)}applyMatrix4(e,t){let n=t||uf.getNormalMatrix(e),r=this.coplanarPoint(pl).applyMatrix4(e),s=this.normal.applyMatrix3(n).normalize();return this.constant=-r.dot(s),this}translate(e){return this.constant-=e.dot(this.normal),this}equals(e){return e.normal.equals(this.normal)&&e.constant===this.constant}clone(){return new this.constructor().copy(this)}},wi=new li,hf=new We(.5,.5),Zs=new D,gr=class{constructor(e=new An,t=new An,n=new An,r=new An,s=new An,a=new An){this.planes=[e,t,n,r,s,a]}set(e,t,n,r,s,a){let o=this.planes;return o[0].copy(e),o[1].copy(t),o[2].copy(n),o[3].copy(r),o[4].copy(s),o[5].copy(a),this}copy(e){let t=this.planes;for(let n=0;n<6;n++)t[n].copy(e.planes[n]);return this}setFromProjectionMatrix(e,t=vn,n=!1){let r=this.planes,s=e.elements,a=s[0],o=s[1],c=s[2],l=s[3],u=s[4],d=s[5],h=s[6],p=s[7],g=s[8],x=s[9],m=s[10],f=s[11],S=s[12],M=s[13],y=s[14],C=s[15];if(r[0].setComponents(l-a,p-u,f-g,C-S).normalize(),r[1].setComponents(l+a,p+u,f+g,C+S).normalize(),r[2].setComponents(l+o,p+d,f+x,C+M).normalize(),r[3].setComponents(l-o,p-d,f-x,C-M).normalize(),n)r[4].setComponents(c,h,m,y).normalize(),r[5].setComponents(l-c,p-h,f-m,C-y).normalize();else if(r[4].setComponents(l-c,p-h,f-m,C-y).normalize(),t===vn)r[5].setComponents(l+c,p+h,f+m,C+y).normalize();else if(t===Vr)r[5].setComponents(c,h,m,y).normalize();else throw new Error("THREE.Frustum.setFromProjectionMatrix(): Invalid coordinate system: "+t);return this}intersectsObject(e){if(e.boundingSphere!==void 0)e.boundingSphere===null&&e.computeBoundingSphere(),wi.copy(e.boundingSphere).applyMatrix4(e.matrixWorld);else{let t=e.geometry;t.boundingSphere===null&&t.computeBoundingSphere(),wi.copy(t.boundingSphere).applyMatrix4(e.matrixWorld)}return this.intersectsSphere(wi)}intersectsSprite(e){wi.center.set(0,0,0);let t=hf.distanceTo(e.center);return wi.radius=.7071067811865476+t,wi.applyMatrix4(e.matrixWorld),this.intersectsSphere(wi)}intersectsSphere(e){let t=this.planes,n=e.center,r=-e.radius;for(let s=0;s<6;s++)if(t[s].distanceToPoint(n)<r)return!1;return!0}intersectsBox(e){let t=this.planes;for(let n=0;n<6;n++){let r=t[n];if(Zs.x=r.normal.x>0?e.max.x:e.min.x,Zs.y=r.normal.y>0?e.max.y:e.min.y,Zs.z=r.normal.z>0?e.max.z:e.min.z,r.distanceToPoint(Zs)<0)return!1}return!0}containsPoint(e){let t=this.planes;for(let n=0;n<6;n++)if(t[n].distanceToPoint(e)<0)return!1;return!0}clone(){return new this.constructor().copy(this)}};var nn=class extends wn{constructor(e){super(),this.isLineBasicMaterial=!0,this.type="LineBasicMaterial",this.color=new Be(16777215),this.map=null,this.linewidth=1,this.linecap="round",this.linejoin="round",this.fog=!0,this.setValues(e)}copy(e){return super.copy(e),this.color.copy(e.color),this.map=e.map,this.linewidth=e.linewidth,this.linecap=e.linecap,this.linejoin=e.linejoin,this.fog=e.fog,this}},_a=new D,ya=new D,ad=new ht,Br=new fr,Js=new li,ml=new D,od=new D,Xn=class extends Mt{constructor(e=new ft,t=new nn){super(),this.isLine=!0,this.type="Line",this.geometry=e,this.material=t,this.morphTargetDictionary=void 0,this.morphTargetInfluences=void 0,this.updateMorphTargets()}copy(e,t){return super.copy(e,t),this.material=Array.isArray(e.material)?e.material.slice():e.material,this.geometry=e.geometry,this}computeLineDistances(){let e=this.geometry;if(e.index===null){let t=e.attributes.position,n=[0];for(let r=1,s=t.count;r<s;r++)_a.fromBufferAttribute(t,r-1),ya.fromBufferAttribute(t,r),n[r]=n[r-1],n[r]+=_a.distanceTo(ya);e.setAttribute("lineDistance",new nt(n,1))}else console.warn("THREE.Line.computeLineDistances(): Computation only possible with non-indexed BufferGeometry.");return this}raycast(e,t){let n=this.geometry,r=this.matrixWorld,s=e.params.Line.threshold,a=n.drawRange;if(n.boundingSphere===null&&n.computeBoundingSphere(),Js.copy(n.boundingSphere),Js.applyMatrix4(r),Js.radius+=s,e.ray.intersectsSphere(Js)===!1)return;ad.copy(r).invert(),Br.copy(e.ray).applyMatrix4(ad);let o=s/((this.scale.x+this.scale.y+this.scale.z)/3),c=o*o,l=this.isLineSegments?2:1,u=n.index,h=n.attributes.position;if(u!==null){let p=Math.max(0,a.start),g=Math.min(u.count,a.start+a.count);for(let x=p,m=g-1;x<m;x+=l){let f=u.getX(x),S=u.getX(x+1),M=Ks(this,e,Br,c,f,S,x);M&&t.push(M)}if(this.isLineLoop){let x=u.getX(g-1),m=u.getX(p),f=Ks(this,e,Br,c,x,m,g-1);f&&t.push(f)}}else{let p=Math.max(0,a.start),g=Math.min(h.count,a.start+a.count);for(let x=p,m=g-1;x<m;x+=l){let f=Ks(this,e,Br,c,x,x+1,x);f&&t.push(f)}if(this.isLineLoop){let x=Ks(this,e,Br,c,g-1,p,g-1);x&&t.push(x)}}}updateMorphTargets(){let t=this.geometry.morphAttributes,n=Object.keys(t);if(n.length>0){let r=t[n[0]];if(r!==void 0){this.morphTargetInfluences=[],this.morphTargetDictionary={};for(let s=0,a=r.length;s<a;s++){let o=r[s].name||String(s);this.morphTargetInfluences.push(0),this.morphTargetDictionary[o]=s}}}}};function Ks(i,e,t,n,r,s,a){let o=i.geometry.attributes.position;if(_a.fromBufferAttribute(o,r),ya.fromBufferAttribute(o,s),t.distanceSqToSegment(_a,ya,ml,od)>n)return;ml.applyMatrix4(i.matrixWorld);let l=e.ray.origin.distanceTo(ml);if(!(l<e.near||l>e.far))return{distance:l,point:od.clone().applyMatrix4(i.matrixWorld),index:a,face:null,faceIndex:null,barycoord:null,object:i}}var ld=new D,cd=new D,ci=class extends Xn{constructor(e,t){super(e,t),this.isLineSegments=!0,this.type="LineSegments"}computeLineDistances(){let e=this.geometry;if(e.index===null){let t=e.attributes.position,n=[];for(let r=0,s=t.count;r<s;r+=2)ld.fromBufferAttribute(t,r),cd.fromBufferAttribute(t,r+1),n[r]=r===0?0:n[r-1],n[r+1]=n[r]+ld.distanceTo(cd);e.setAttribute("lineDistance",new nt(n,1))}else console.warn("THREE.LineSegments.computeLineDistances(): Computation only possible with non-indexed BufferGeometry.");return this}};var va=class extends wn{constructor(e){super(),this.isPointsMaterial=!0,this.type="PointsMaterial",this.color=new Be(16777215),this.map=null,this.alphaMap=null,this.size=1,this.sizeAttenuation=!0,this.fog=!0,this.setValues(e)}copy(e){return super.copy(e),this.color.copy(e.color),this.map=e.map,this.alphaMap=e.alphaMap,this.size=e.size,this.sizeAttenuation=e.sizeAttenuation,this.fog=e.fog,this}},dd=new ht,Ml=new fr,js=new li,Qs=new D,Qr=class extends Mt{constructor(e=new ft,t=new va){super(),this.isPoints=!0,this.type="Points",this.geometry=e,this.material=t,this.morphTargetDictionary=void 0,this.morphTargetInfluences=void 0,this.updateMorphTargets()}copy(e,t){return super.copy(e,t),this.material=Array.isArray(e.material)?e.material.slice():e.material,this.geometry=e.geometry,this}raycast(e,t){let n=this.geometry,r=this.matrixWorld,s=e.params.Points.threshold,a=n.drawRange;if(n.boundingSphere===null&&n.computeBoundingSphere(),js.copy(n.boundingSphere),js.applyMatrix4(r),js.radius+=s,e.ray.intersectsSphere(js)===!1)return;dd.copy(r).invert(),Ml.copy(e.ray).applyMatrix4(dd);let o=s/((this.scale.x+this.scale.y+this.scale.z)/3),c=o*o,l=n.index,d=n.attributes.position;if(l!==null){let h=Math.max(0,a.start),p=Math.min(l.count,a.start+a.count);for(let g=h,x=p;g<x;g++){let m=l.getX(g);Qs.fromBufferAttribute(d,m),ud(Qs,m,c,r,e,t,this)}}else{let h=Math.max(0,a.start),p=Math.min(d.count,a.start+a.count);for(let g=h,x=p;g<x;g++)Qs.fromBufferAttribute(d,g),ud(Qs,g,c,r,e,t,this)}}updateMorphTargets(){let t=this.geometry.morphAttributes,n=Object.keys(t);if(n.length>0){let r=t[n[0]];if(r!==void 0){this.morphTargetInfluences=[],this.morphTargetDictionary={};for(let s=0,a=r.length;s<a;s++){let o=r[s].name||String(s);this.morphTargetInfluences.push(0),this.morphTargetDictionary[o]=s}}}}};function ud(i,e,t,n,r,s,a){let o=Ml.distanceSqToPoint(i);if(o<t){let c=new D;Ml.closestPointToPoint(i,c),c.applyMatrix4(n);let l=r.ray.origin.distanceTo(c);if(l<r.near||l>r.far)return;s.push({distance:l,distanceToRay:Math.sqrt(o),point:c,index:e,face:null,faceIndex:null,barycoord:null,object:a})}}var es=class extends Lt{constructor(e,t,n,r,s,a,o,c,l){super(e,t,n,r,s,a,o,c,l),this.isCanvasTexture=!0,this.needsUpdate=!0}},ts=class extends Lt{constructor(e,t,n=pi,r,s,a,o=dn,c=dn,l,u=cr,d=1){if(u!==cr&&u!==br)throw new Error("DepthTexture format must be either THREE.DepthFormat or THREE.DepthStencilFormat");let h={width:e,height:t,depth:d};super(h,r,s,a,o,c,u,n,l),this.isDepthTexture=!0,this.flipY=!1,this.generateMipmaps=!1,this.compareFunction=null}copy(e){return super.copy(e),this.source=new hr(Object.assign({},e.image)),this.compareFunction=e.compareFunction,this}toJSON(e){let t=super.toJSON(e);return this.compareFunction!==null&&(t.compareFunction=this.compareFunction),t}},ns=class extends Lt{constructor(e=null){super(),this.sourceTexture=e,this.isExternalTexture=!0}copy(e){return super.copy(e),this.sourceTexture=e.sourceTexture,this}};var In=class i extends ft{constructor(e=1,t=1,n=1,r=32,s=1,a=!1,o=0,c=Math.PI*2){super(),this.type="CylinderGeometry",this.parameters={radiusTop:e,radiusBottom:t,height:n,radialSegments:r,heightSegments:s,openEnded:a,thetaStart:o,thetaLength:c};let l=this;r=Math.floor(r),s=Math.floor(s);let u=[],d=[],h=[],p=[],g=0,x=[],m=n/2,f=0;S(),a===!1&&(e>0&&M(!0),t>0&&M(!1)),this.setIndex(u),this.setAttribute("position",new nt(d,3)),this.setAttribute("normal",new nt(h,3)),this.setAttribute("uv",new nt(p,2));function S(){let y=new D,C=new D,A=0,I=(t-e)/n;for(let N=0;N<=s;N++){let v=[],b=N/s,T=b*(t-e)+e;for(let P=0;P<=r;P++){let U=P/r,F=U*c+o,k=Math.sin(F),G=Math.cos(F);C.x=T*k,C.y=-b*n+m,C.z=T*G,d.push(C.x,C.y,C.z),y.set(k,I,G).normalize(),h.push(y.x,y.y,y.z),p.push(U,1-b),v.push(g++)}x.push(v)}for(let N=0;N<r;N++)for(let v=0;v<s;v++){let b=x[v][N],T=x[v+1][N],P=x[v+1][N+1],U=x[v][N+1];(e>0||v!==0)&&(u.push(b,T,U),A+=3),(t>0||v!==s-1)&&(u.push(T,P,U),A+=3)}l.addGroup(f,A,0),f+=A}function M(y){let C=g,A=new We,I=new D,N=0,v=y===!0?e:t,b=y===!0?1:-1;for(let P=1;P<=r;P++)d.push(0,m*b,0),h.push(0,b,0),p.push(.5,.5),g++;let T=g;for(let P=0;P<=r;P++){let F=P/r*c+o,k=Math.cos(F),G=Math.sin(F);I.x=v*G,I.y=m*b,I.z=v*k,d.push(I.x,I.y,I.z),h.push(0,b,0),A.x=k*.5+.5,A.y=G*.5*b+.5,p.push(A.x,A.y),g++}for(let P=0;P<r;P++){let U=C+P,F=T+P;y===!0?u.push(F,F+1,U):u.push(F+1,F,U),N+=3}l.addGroup(f,N,y===!0?1:2),f+=N}}copy(e){return super.copy(e),this.parameters=Object.assign({},e.parameters),this}static fromJSON(e){return new i(e.radiusTop,e.radiusBottom,e.height,e.radialSegments,e.heightSegments,e.openEnded,e.thetaStart,e.thetaLength)}},xr=class i extends In{constructor(e=1,t=1,n=32,r=1,s=!1,a=0,o=Math.PI*2){super(0,e,t,n,r,s,a,o),this.type="ConeGeometry",this.parameters={radius:e,height:t,radialSegments:n,heightSegments:r,openEnded:s,thetaStart:a,thetaLength:o}}static fromJSON(e){return new i(e.radius,e.height,e.radialSegments,e.heightSegments,e.openEnded,e.thetaStart,e.thetaLength)}};var ea=new D,ta=new D,gl=new D,na=new Cn,is=class extends ft{constructor(e=null,t=1){if(super(),this.type="EdgesGeometry",this.parameters={geometry:e,thresholdAngle:t},e!==null){let r=Math.pow(10,4),s=Math.cos(or*t),a=e.getIndex(),o=e.getAttribute("position"),c=a?a.count:o.count,l=[0,0,0],u=["a","b","c"],d=new Array(3),h={},p=[];for(let g=0;g<c;g+=3){a?(l[0]=a.getX(g),l[1]=a.getX(g+1),l[2]=a.getX(g+2)):(l[0]=g,l[1]=g+1,l[2]=g+2);let{a:x,b:m,c:f}=na;if(x.fromBufferAttribute(o,l[0]),m.fromBufferAttribute(o,l[1]),f.fromBufferAttribute(o,l[2]),na.getNormal(gl),d[0]=`${Math.round(x.x*r)},${Math.round(x.y*r)},${Math.round(x.z*r)}`,d[1]=`${Math.round(m.x*r)},${Math.round(m.y*r)},${Math.round(m.z*r)}`,d[2]=`${Math.round(f.x*r)},${Math.round(f.y*r)},${Math.round(f.z*r)}`,!(d[0]===d[1]||d[1]===d[2]||d[2]===d[0]))for(let S=0;S<3;S++){let M=(S+1)%3,y=d[S],C=d[M],A=na[u[S]],I=na[u[M]],N=`${y}_${C}`,v=`${C}_${y}`;v in h&&h[v]?(gl.dot(h[v].normal)<=s&&(p.push(A.x,A.y,A.z),p.push(I.x,I.y,I.z)),h[v]=null):N in h||(h[N]={index0:l[S],index1:l[M],normal:gl.clone()})}}for(let g in h)if(h[g]){let{index0:x,index1:m}=h[g];ea.fromBufferAttribute(o,x),ta.fromBufferAttribute(o,m),p.push(ea.x,ea.y,ea.z),p.push(ta.x,ta.y,ta.z)}this.setAttribute("position",new nt(p,3))}}copy(e){return super.copy(e),this.parameters=Object.assign({},e.parameters),this}};var Ai=class i extends ft{constructor(e=1,t=1,n=1,r=1){super(),this.type="PlaneGeometry",this.parameters={width:e,height:t,widthSegments:n,heightSegments:r};let s=e/2,a=t/2,o=Math.floor(n),c=Math.floor(r),l=o+1,u=c+1,d=e/o,h=t/c,p=[],g=[],x=[],m=[];for(let f=0;f<u;f++){let S=f*h-a;for(let M=0;M<l;M++){let y=M*d-s;g.push(y,-S,0),x.push(0,0,1),m.push(M/o),m.push(1-f/c)}}for(let f=0;f<c;f++)for(let S=0;S<o;S++){let M=S+l*f,y=S+l*(f+1),C=S+1+l*(f+1),A=S+1+l*f;p.push(M,y,A),p.push(y,C,A)}this.setIndex(p),this.setAttribute("position",new nt(g,3)),this.setAttribute("normal",new nt(x,3)),this.setAttribute("uv",new nt(m,2))}copy(e){return super.copy(e),this.parameters=Object.assign({},e.parameters),this}static fromJSON(e){return new i(e.width,e.height,e.widthSegments,e.heightSegments)}};var di=class i extends ft{constructor(e=1,t=32,n=16,r=0,s=Math.PI*2,a=0,o=Math.PI){super(),this.type="SphereGeometry",this.parameters={radius:e,widthSegments:t,heightSegments:n,phiStart:r,phiLength:s,thetaStart:a,thetaLength:o},t=Math.max(3,Math.floor(t)),n=Math.max(2,Math.floor(n));let c=Math.min(a+o,Math.PI),l=0,u=[],d=new D,h=new D,p=[],g=[],x=[],m=[];for(let f=0;f<=n;f++){let S=[],M=f/n,y=0;f===0&&a===0?y=.5/t:f===n&&c===Math.PI&&(y=-.5/t);for(let C=0;C<=t;C++){let A=C/t;d.x=-e*Math.cos(r+A*s)*Math.sin(a+M*o),d.y=e*Math.cos(a+M*o),d.z=e*Math.sin(r+A*s)*Math.sin(a+M*o),g.push(d.x,d.y,d.z),h.copy(d).normalize(),x.push(h.x,h.y,h.z),m.push(A+y,1-M),S.push(l++)}u.push(S)}for(let f=0;f<n;f++)for(let S=0;S<t;S++){let M=u[f][S+1],y=u[f][S],C=u[f+1][S],A=u[f+1][S+1];(f!==0||a>0)&&p.push(M,y,A),(f!==n-1||c<Math.PI)&&p.push(y,C,A)}this.setIndex(p),this.setAttribute("position",new nt(g,3)),this.setAttribute("normal",new nt(x,3)),this.setAttribute("uv",new nt(m,2))}copy(e){return super.copy(e),this.parameters=Object.assign({},e.parameters),this}static fromJSON(e){return new i(e.radius,e.widthSegments,e.heightSegments,e.phiStart,e.phiLength,e.thetaStart,e.thetaLength)}};var rs=class extends wn{constructor(e){super(),this.isMeshStandardMaterial=!0,this.type="MeshStandardMaterial",this.defines={STANDARD:""},this.color=new Be(16777215),this.roughness=1,this.metalness=0,this.map=null,this.lightMap=null,this.lightMapIntensity=1,this.aoMap=null,this.aoMapIntensity=1,this.emissive=new Be(0),this.emissiveIntensity=1,this.emissiveMap=null,this.bumpMap=null,this.bumpScale=1,this.normalMap=null,this.normalMapType=Vl,this.normalScale=new We(1,1),this.displacementMap=null,this.displacementScale=1,this.displacementBias=0,this.roughnessMap=null,this.metalnessMap=null,this.alphaMap=null,this.envMap=null,this.envMapRotation=new en,this.envMapIntensity=1,this.wireframe=!1,this.wireframeLinewidth=1,this.wireframeLinecap="round",this.wireframeLinejoin="round",this.flatShading=!1,this.fog=!0,this.setValues(e)}copy(e){return super.copy(e),this.defines={STANDARD:""},this.color.copy(e.color),this.roughness=e.roughness,this.metalness=e.metalness,this.map=e.map,this.lightMap=e.lightMap,this.lightMapIntensity=e.lightMapIntensity,this.aoMap=e.aoMap,this.aoMapIntensity=e.aoMapIntensity,this.emissive.copy(e.emissive),this.emissiveMap=e.emissiveMap,this.emissiveIntensity=e.emissiveIntensity,this.bumpMap=e.bumpMap,this.bumpScale=e.bumpScale,this.normalMap=e.normalMap,this.normalMapType=e.normalMapType,this.normalScale.copy(e.normalScale),this.displacementMap=e.displacementMap,this.displacementScale=e.displacementScale,this.displacementBias=e.displacementBias,this.roughnessMap=e.roughnessMap,this.metalnessMap=e.metalnessMap,this.alphaMap=e.alphaMap,this.envMap=e.envMap,this.envMapRotation.copy(e.envMapRotation),this.envMapIntensity=e.envMapIntensity,this.wireframe=e.wireframe,this.wireframeLinewidth=e.wireframeLinewidth,this.wireframeLinecap=e.wireframeLinecap,this.wireframeLinejoin=e.wireframeLinejoin,this.flatShading=e.flatShading,this.fog=e.fog,this}};var ba=class extends wn{constructor(e){super(),this.isMeshDepthMaterial=!0,this.type="MeshDepthMaterial",this.depthPacking=$d,this.map=null,this.alphaMap=null,this.displacementMap=null,this.displacementScale=1,this.displacementBias=0,this.wireframe=!1,this.wireframeLinewidth=1,this.setValues(e)}copy(e){return super.copy(e),this.depthPacking=e.depthPacking,this.map=e.map,this.alphaMap=e.alphaMap,this.displacementMap=e.displacementMap,this.displacementScale=e.displacementScale,this.displacementBias=e.displacementBias,this.wireframe=e.wireframe,this.wireframeLinewidth=e.wireframeLinewidth,this}},wa=class extends wn{constructor(e){super(),this.isMeshDistanceMaterial=!0,this.type="MeshDistanceMaterial",this.map=null,this.alphaMap=null,this.displacementMap=null,this.displacementScale=1,this.displacementBias=0,this.setValues(e)}copy(e){return super.copy(e),this.map=e.map,this.alphaMap=e.alphaMap,this.displacementMap=e.displacementMap,this.displacementScale=e.displacementScale,this.displacementBias=e.displacementBias,this}};function ia(i,e){return!i||i.constructor===e?i:typeof e.BYTES_PER_ELEMENT=="number"?new e(i):Array.prototype.slice.call(i)}function ff(i){return ArrayBuffer.isView(i)&&!(i instanceof DataView)}var Ci=class{constructor(e,t,n,r){this.parameterPositions=e,this._cachedIndex=0,this.resultBuffer=r!==void 0?r:new t.constructor(n),this.sampleValues=t,this.valueSize=n,this.settings=null,this.DefaultSettings_={}}evaluate(e){let t=this.parameterPositions,n=this._cachedIndex,r=t[n],s=t[n-1];n:{e:{let a;t:{i:if(!(e<r)){for(let o=n+2;;){if(r===void 0){if(e<s)break i;return n=t.length,this._cachedIndex=n,this.copySampleValue_(n-1)}if(n===o)break;if(s=r,r=t[++n],e<r)break e}a=t.length;break t}if(!(e>=s)){let o=t[1];e<o&&(n=2,s=o);for(let c=n-2;;){if(s===void 0)return this._cachedIndex=0,this.copySampleValue_(0);if(n===c)break;if(r=s,s=t[--n-1],e>=s)break e}a=n,n=0;break t}break n}for(;n<a;){let o=n+a>>>1;e<t[o]?a=o:n=o+1}if(r=t[n],s=t[n-1],s===void 0)return this._cachedIndex=0,this.copySampleValue_(0);if(r===void 0)return n=t.length,this._cachedIndex=n,this.copySampleValue_(n-1)}this._cachedIndex=n,this.intervalChanged_(n,s,r)}return this.interpolate_(n,s,e,r)}getSettings_(){return this.settings||this.DefaultSettings_}copySampleValue_(e){let t=this.resultBuffer,n=this.sampleValues,r=this.valueSize,s=e*r;for(let a=0;a!==r;++a)t[a]=n[s+a];return t}interpolate_(){throw new Error("call to abstract method")}intervalChanged_(){}},Ma=class extends Ci{constructor(e,t,n,r){super(e,t,n,r),this._weightPrev=-0,this._offsetPrev=-0,this._weightNext=-0,this._offsetNext=-0,this.DefaultSettings_={endingStart:yl,endingEnd:yl}}intervalChanged_(e,t,n){let r=this.parameterPositions,s=e-2,a=e+1,o=r[s],c=r[a];if(o===void 0)switch(this.getSettings_().endingStart){case vl:s=e,o=2*t-n;break;case bl:s=r.length-2,o=t+r[s]-r[s+1];break;default:s=e,o=n}if(c===void 0)switch(this.getSettings_().endingEnd){case vl:a=e,c=2*n-t;break;case bl:a=1,c=n+r[1]-r[0];break;default:a=e-1,c=t}let l=(n-t)*.5,u=this.valueSize;this._weightPrev=l/(t-o),this._weightNext=l/(c-n),this._offsetPrev=s*u,this._offsetNext=a*u}interpolate_(e,t,n,r){let s=this.resultBuffer,a=this.sampleValues,o=this.valueSize,c=e*o,l=c-o,u=this._offsetPrev,d=this._offsetNext,h=this._weightPrev,p=this._weightNext,g=(n-t)/(r-t),x=g*g,m=x*g,f=-h*m+2*h*x-h*g,S=(1+h)*m+(-1.5-2*h)*x+(-.5+h)*g+1,M=(-1-p)*m+(1.5+p)*x+.5*g,y=p*m-p*x;for(let C=0;C!==o;++C)s[C]=f*a[u+C]+S*a[l+C]+M*a[c+C]+y*a[d+C];return s}},Sa=class extends Ci{constructor(e,t,n,r){super(e,t,n,r)}interpolate_(e,t,n,r){let s=this.resultBuffer,a=this.sampleValues,o=this.valueSize,c=e*o,l=c-o,u=(n-t)/(r-t),d=1-u;for(let h=0;h!==o;++h)s[h]=a[l+h]*d+a[c+h]*u;return s}},Ea=class extends Ci{constructor(e,t,n,r){super(e,t,n,r)}interpolate_(e){return this.copySampleValue_(e-1)}},rn=class{constructor(e,t,n,r){if(e===void 0)throw new Error("THREE.KeyframeTrack: track name is undefined");if(t===void 0||t.length===0)throw new Error("THREE.KeyframeTrack: no keyframes in track named "+e);this.name=e,this.times=ia(t,this.TimeBufferType),this.values=ia(n,this.ValueBufferType),this.setInterpolation(r||this.DefaultInterpolation)}static toJSON(e){let t=e.constructor,n;if(t.toJSON!==this.toJSON)n=t.toJSON(e);else{n={name:e.name,times:ia(e.times,Array),values:ia(e.values,Array)};let r=e.getInterpolation();r!==e.DefaultInterpolation&&(n.interpolation=r)}return n.type=e.ValueTypeName,n}InterpolantFactoryMethodDiscrete(e){return new Ea(this.times,this.values,this.getValueSize(),e)}InterpolantFactoryMethodLinear(e){return new Sa(this.times,this.values,this.getValueSize(),e)}InterpolantFactoryMethodSmooth(e){return new Ma(this.times,this.values,this.getValueSize(),e)}setInterpolation(e){let t;switch(e){case kr:t=this.InterpolantFactoryMethodDiscrete;break;case da:t=this.InterpolantFactoryMethodLinear;break;case sa:t=this.InterpolantFactoryMethodSmooth;break}if(t===void 0){let n="unsupported interpolation for "+this.ValueTypeName+" keyframe track named "+this.name;if(this.createInterpolant===void 0)if(e!==this.DefaultInterpolation)this.setInterpolation(this.DefaultInterpolation);else throw new Error(n);return console.warn("THREE.KeyframeTrack:",n),this}return this.createInterpolant=t,this}getInterpolation(){switch(this.createInterpolant){case this.InterpolantFactoryMethodDiscrete:return kr;case this.InterpolantFactoryMethodLinear:return da;case this.InterpolantFactoryMethodSmooth:return sa}}getValueSize(){return this.values.length/this.times.length}shift(e){if(e!==0){let t=this.times;for(let n=0,r=t.length;n!==r;++n)t[n]+=e}return this}scale(e){if(e!==1){let t=this.times;for(let n=0,r=t.length;n!==r;++n)t[n]*=e}return this}trim(e,t){let n=this.times,r=n.length,s=0,a=r-1;for(;s!==r&&n[s]<e;)++s;for(;a!==-1&&n[a]>t;)--a;if(++a,s!==0||a!==r){s>=a&&(a=Math.max(a,1),s=a-1);let o=this.getValueSize();this.times=n.slice(s,a),this.values=this.values.slice(s*o,a*o)}return this}validate(){let e=!0,t=this.getValueSize();t-Math.floor(t)!==0&&(console.error("THREE.KeyframeTrack: Invalid value size in track.",this),e=!1);let n=this.times,r=this.values,s=n.length;s===0&&(console.error("THREE.KeyframeTrack: Track is empty.",this),e=!1);let a=null;for(let o=0;o!==s;o++){let c=n[o];if(typeof c=="number"&&isNaN(c)){console.error("THREE.KeyframeTrack: Time is not a valid number.",this,o,c),e=!1;break}if(a!==null&&a>c){console.error("THREE.KeyframeTrack: Out of order keys.",this,o,c,a),e=!1;break}a=c}if(r!==void 0&&ff(r))for(let o=0,c=r.length;o!==c;++o){let l=r[o];if(isNaN(l)){console.error("THREE.KeyframeTrack: Value is not a valid number.",this,o,l),e=!1;break}}return e}optimize(){let e=this.times.slice(),t=this.values.slice(),n=this.getValueSize(),r=this.getInterpolation()===sa,s=e.length-1,a=1;for(let o=1;o<s;++o){let c=!1,l=e[o],u=e[o+1];if(l!==u&&(o!==1||l!==e[0]))if(r)c=!0;else{let d=o*n,h=d-n,p=d+n;for(let g=0;g!==n;++g){let x=t[d+g];if(x!==t[h+g]||x!==t[p+g]){c=!0;break}}}if(c){if(o!==a){e[a]=e[o];let d=o*n,h=a*n;for(let p=0;p!==n;++p)t[h+p]=t[d+p]}++a}}if(s>0){e[a]=e[s];for(let o=s*n,c=a*n,l=0;l!==n;++l)t[c+l]=t[o+l];++a}return a!==e.length?(this.times=e.slice(0,a),this.values=t.slice(0,a*n)):(this.times=e,this.values=t),this}clone(){let e=this.times.slice(),t=this.values.slice(),n=this.constructor,r=new n(this.name,e,t);return r.createInterpolant=this.createInterpolant,r}};rn.prototype.ValueTypeName="";rn.prototype.TimeBufferType=Float32Array;rn.prototype.ValueBufferType=Float32Array;rn.prototype.DefaultInterpolation=da;var ui=class extends rn{constructor(e,t,n){super(e,t,n)}};ui.prototype.ValueTypeName="bool";ui.prototype.ValueBufferType=Array;ui.prototype.DefaultInterpolation=kr;ui.prototype.InterpolantFactoryMethodLinear=void 0;ui.prototype.InterpolantFactoryMethodSmooth=void 0;var Ta=class extends rn{constructor(e,t,n,r){super(e,t,n,r)}};Ta.prototype.ValueTypeName="color";var Aa=class extends rn{constructor(e,t,n,r){super(e,t,n,r)}};Aa.prototype.ValueTypeName="number";var Ca=class extends Ci{constructor(e,t,n,r){super(e,t,n,r)}interpolate_(e,t,n,r){let s=this.resultBuffer,a=this.sampleValues,o=this.valueSize,c=(n-t)/(r-t),l=e*o;for(let u=l+o;l!==u;l+=4)Gt.slerpFlat(s,0,a,l-o,a,l,c);return s}},ss=class extends rn{constructor(e,t,n,r){super(e,t,n,r)}InterpolantFactoryMethodLinear(e){return new Ca(this.times,this.values,this.getValueSize(),e)}};ss.prototype.ValueTypeName="quaternion";ss.prototype.InterpolantFactoryMethodSmooth=void 0;var hi=class extends rn{constructor(e,t,n){super(e,t,n)}};hi.prototype.ValueTypeName="string";hi.prototype.ValueBufferType=Array;hi.prototype.DefaultInterpolation=kr;hi.prototype.InterpolantFactoryMethodLinear=void 0;hi.prototype.InterpolantFactoryMethodSmooth=void 0;var Ra=class extends rn{constructor(e,t,n,r){super(e,t,n,r)}};Ra.prototype.ValueTypeName="vector";var Ia=class{constructor(e,t,n){let r=this,s=!1,a=0,o=0,c,l=[];this.onStart=void 0,this.onLoad=e,this.onProgress=t,this.onError=n,this.abortController=new AbortController,this.itemStart=function(u){o++,s===!1&&r.onStart!==void 0&&r.onStart(u,a,o),s=!0},this.itemEnd=function(u){a++,r.onProgress!==void 0&&r.onProgress(u,a,o),a===o&&(s=!1,r.onLoad!==void 0&&r.onLoad())},this.itemError=function(u){r.onError!==void 0&&r.onError(u)},this.resolveURL=function(u){return c?c(u):u},this.setURLModifier=function(u){return c=u,this},this.addHandler=function(u,d){return l.push(u,d),this},this.removeHandler=function(u){let d=l.indexOf(u);return d!==-1&&l.splice(d,2),this},this.getHandler=function(u){for(let d=0,h=l.length;d<h;d+=2){let p=l[d],g=l[d+1];if(p.global&&(p.lastIndex=0),p.test(u))return g}return null},this.abort=function(){return this.abortController.abort(),this.abortController=new AbortController,this}}},ou=new Ia,Pa=class{constructor(e){this.manager=e!==void 0?e:ou,this.crossOrigin="anonymous",this.withCredentials=!1,this.path="",this.resourcePath="",this.requestHeader={}}load(){}loadAsync(e,t){let n=this;return new Promise(function(r,s){n.load(e,r,t,s)})}parse(){}setCrossOrigin(e){return this.crossOrigin=e,this}setWithCredentials(e){return this.withCredentials=e,this}setPath(e){return this.path=e,this}setResourcePath(e){return this.resourcePath=e,this}setRequestHeader(e){return this.requestHeader=e,this}abort(){return this}};Pa.DEFAULT_MATERIAL_NAME="__DEFAULT";var as=class extends Mt{constructor(e,t=1){super(),this.isLight=!0,this.type="Light",this.color=new Be(e),this.intensity=t}dispose(){}copy(e,t){return super.copy(e,t),this.color.copy(e.color),this.intensity=e.intensity,this}toJSON(e){let t=super.toJSON(e);return t.object.color=this.color.getHex(),t.object.intensity=this.intensity,this.groundColor!==void 0&&(t.object.groundColor=this.groundColor.getHex()),this.distance!==void 0&&(t.object.distance=this.distance),this.angle!==void 0&&(t.object.angle=this.angle),this.decay!==void 0&&(t.object.decay=this.decay),this.penumbra!==void 0&&(t.object.penumbra=this.penumbra),this.shadow!==void 0&&(t.object.shadow=this.shadow.toJSON()),this.target!==void 0&&(t.object.target=this.target.uuid),t}},os=class extends as{constructor(e,t,n){super(e,n),this.isHemisphereLight=!0,this.type="HemisphereLight",this.position.copy(Mt.DEFAULT_UP),this.updateMatrix(),this.groundColor=new Be(t)}copy(e,t){return super.copy(e,t),this.groundColor.copy(e.groundColor),this}},xl=new ht,hd=new D,fd=new D,Sl=class{constructor(e){this.camera=e,this.intensity=1,this.bias=0,this.normalBias=0,this.radius=1,this.blurSamples=8,this.mapSize=new We(512,512),this.mapType=Sn,this.map=null,this.mapPass=null,this.matrix=new ht,this.autoUpdate=!0,this.needsUpdate=!1,this._frustum=new gr,this._frameExtents=new We(1,1),this._viewportCount=1,this._viewports=[new xt(0,0,1,1)]}getViewportCount(){return this._viewportCount}getFrustum(){return this._frustum}updateMatrices(e){let t=this.camera,n=this.matrix;hd.setFromMatrixPosition(e.matrixWorld),t.position.copy(hd),fd.setFromMatrixPosition(e.target.matrixWorld),t.lookAt(fd),t.updateMatrixWorld(),xl.multiplyMatrices(t.projectionMatrix,t.matrixWorldInverse),this._frustum.setFromProjectionMatrix(xl,t.coordinateSystem,t.reversedDepth),t.reversedDepth?n.set(.5,0,0,.5,0,.5,0,.5,0,0,1,0,0,0,0,1):n.set(.5,0,0,.5,0,.5,0,.5,0,0,.5,.5,0,0,0,1),n.multiply(xl)}getViewport(e){return this._viewports[e]}getFrameExtents(){return this._frameExtents}dispose(){this.map&&this.map.dispose(),this.mapPass&&this.mapPass.dispose()}copy(e){return this.camera=e.camera.clone(),this.intensity=e.intensity,this.bias=e.bias,this.radius=e.radius,this.autoUpdate=e.autoUpdate,this.needsUpdate=e.needsUpdate,this.normalBias=e.normalBias,this.blurSamples=e.blurSamples,this.mapSize.copy(e.mapSize),this}clone(){return new this.constructor().copy(this)}toJSON(){let e={};return this.intensity!==1&&(e.intensity=this.intensity),this.bias!==0&&(e.bias=this.bias),this.normalBias!==0&&(e.normalBias=this.normalBias),this.radius!==1&&(e.radius=this.radius),(this.mapSize.x!==512||this.mapSize.y!==512)&&(e.mapSize=this.mapSize.toArray()),e.camera=this.camera.toJSON(!1).object,delete e.camera.matrix,e}};var ls=class extends Yr{constructor(e=-1,t=1,n=1,r=-1,s=.1,a=2e3){super(),this.isOrthographicCamera=!0,this.type="OrthographicCamera",this.zoom=1,this.view=null,this.left=e,this.right=t,this.top=n,this.bottom=r,this.near=s,this.far=a,this.updateProjectionMatrix()}copy(e,t){return super.copy(e,t),this.left=e.left,this.right=e.right,this.top=e.top,this.bottom=e.bottom,this.near=e.near,this.far=e.far,this.zoom=e.zoom,this.view=e.view===null?null:Object.assign({},e.view),this}setViewOffset(e,t,n,r,s,a){this.view===null&&(this.view={enabled:!0,fullWidth:1,fullHeight:1,offsetX:0,offsetY:0,width:1,height:1}),this.view.enabled=!0,this.view.fullWidth=e,this.view.fullHeight=t,this.view.offsetX=n,this.view.offsetY=r,this.view.width=s,this.view.height=a,this.updateProjectionMatrix()}clearViewOffset(){this.view!==null&&(this.view.enabled=!1),this.updateProjectionMatrix()}updateProjectionMatrix(){let e=(this.right-this.left)/(2*this.zoom),t=(this.top-this.bottom)/(2*this.zoom),n=(this.right+this.left)/2,r=(this.top+this.bottom)/2,s=n-e,a=n+e,o=r+t,c=r-t;if(this.view!==null&&this.view.enabled){let l=(this.right-this.left)/this.view.fullWidth/this.zoom,u=(this.top-this.bottom)/this.view.fullHeight/this.zoom;s+=l*this.view.offsetX,a=s+l*this.view.width,o-=u*this.view.offsetY,c=o-u*this.view.height}this.projectionMatrix.makeOrthographic(s,a,o,c,this.near,this.far,this.coordinateSystem,this.reversedDepth),this.projectionMatrixInverse.copy(this.projectionMatrix).invert()}toJSON(e){let t=super.toJSON(e);return t.object.zoom=this.zoom,t.object.left=this.left,t.object.right=this.right,t.object.top=this.top,t.object.bottom=this.bottom,t.object.near=this.near,t.object.far=this.far,this.view!==null&&(t.object.view=Object.assign({},this.view)),t}},El=class extends Sl{constructor(){super(new ls(-5,5,5,-5,.5,500)),this.isDirectionalLightShadow=!0}},cs=class extends as{constructor(e,t){super(e,t),this.isDirectionalLight=!0,this.type="DirectionalLight",this.position.copy(Mt.DEFAULT_UP),this.updateMatrix(),this.target=new Mt,this.shadow=new El}dispose(){this.shadow.dispose()}copy(e){return super.copy(e),this.target=e.target.clone(),this.shadow=e.shadow.clone(),this}};var Na=class extends Dt{constructor(e=[]){super(),this.isArrayCamera=!0,this.isMultiViewCamera=!1,this.cameras=e}};var Yl="\\[\\]\\.:\\/",pf=new RegExp("["+Yl+"]","g"),Zl="[^"+Yl+"]",mf="[^"+Yl.replace("\\.","")+"]",gf=/((?:WC+[\/:])*)/.source.replace("WC",Zl),xf=/(WCOD+)?/.source.replace("WCOD",mf),_f=/(?:\.(WC+)(?:\[(.+)\])?)?/.source.replace("WC",Zl),yf=/\.(WC+)(?:\[(.+)\])?/.source.replace("WC",Zl),vf=new RegExp("^"+gf+xf+_f+yf+"$"),bf=["material","materials","bones","map"],Tl=class{constructor(e,t,n){let r=n||ct.parseTrackName(t);this._targetGroup=e,this._bindings=e.subscribe_(t,r)}getValue(e,t){this.bind();let n=this._targetGroup.nCachedObjects_,r=this._bindings[n];r!==void 0&&r.getValue(e,t)}setValue(e,t){let n=this._bindings;for(let r=this._targetGroup.nCachedObjects_,s=n.length;r!==s;++r)n[r].setValue(e,t)}bind(){let e=this._bindings;for(let t=this._targetGroup.nCachedObjects_,n=e.length;t!==n;++t)e[t].bind()}unbind(){let e=this._bindings;for(let t=this._targetGroup.nCachedObjects_,n=e.length;t!==n;++t)e[t].unbind()}},ct=class i{constructor(e,t,n){this.path=t,this.parsedPath=n||i.parseTrackName(t),this.node=i.findNode(e,this.parsedPath.nodeName),this.rootNode=e,this.getValue=this._getValue_unbound,this.setValue=this._setValue_unbound}static create(e,t,n){return e&&e.isAnimationObjectGroup?new i.Composite(e,t,n):new i(e,t,n)}static sanitizeNodeName(e){return e.replace(/\s/g,"_").replace(pf,"")}static parseTrackName(e){let t=vf.exec(e);if(t===null)throw new Error("PropertyBinding: Cannot parse trackName: "+e);let n={nodeName:t[2],objectName:t[3],objectIndex:t[4],propertyName:t[5],propertyIndex:t[6]},r=n.nodeName&&n.nodeName.lastIndexOf(".");if(r!==void 0&&r!==-1){let s=n.nodeName.substring(r+1);bf.indexOf(s)!==-1&&(n.nodeName=n.nodeName.substring(0,r),n.objectName=s)}if(n.propertyName===null||n.propertyName.length===0)throw new Error("PropertyBinding: can not parse propertyName from trackName: "+e);return n}static findNode(e,t){if(t===void 0||t===""||t==="."||t===-1||t===e.name||t===e.uuid)return e;if(e.skeleton){let n=e.skeleton.getBoneByName(t);if(n!==void 0)return n}if(e.children){let n=function(s){for(let a=0;a<s.length;a++){let o=s[a];if(o.name===t||o.uuid===t)return o;let c=n(o.children);if(c)return c}return null},r=n(e.children);if(r)return r}return null}_getValue_unavailable(){}_setValue_unavailable(){}_getValue_direct(e,t){e[t]=this.targetObject[this.propertyName]}_getValue_array(e,t){let n=this.resolvedProperty;for(let r=0,s=n.length;r!==s;++r)e[t++]=n[r]}_getValue_arrayElement(e,t){e[t]=this.resolvedProperty[this.propertyIndex]}_getValue_toArray(e,t){this.resolvedProperty.toArray(e,t)}_setValue_direct(e,t){this.targetObject[this.propertyName]=e[t]}_setValue_direct_setNeedsUpdate(e,t){this.targetObject[this.propertyName]=e[t],this.targetObject.needsUpdate=!0}_setValue_direct_setMatrixWorldNeedsUpdate(e,t){this.targetObject[this.propertyName]=e[t],this.targetObject.matrixWorldNeedsUpdate=!0}_setValue_array(e,t){let n=this.resolvedProperty;for(let r=0,s=n.length;r!==s;++r)n[r]=e[t++]}_setValue_array_setNeedsUpdate(e,t){let n=this.resolvedProperty;for(let r=0,s=n.length;r!==s;++r)n[r]=e[t++];this.targetObject.needsUpdate=!0}_setValue_array_setMatrixWorldNeedsUpdate(e,t){let n=this.resolvedProperty;for(let r=0,s=n.length;r!==s;++r)n[r]=e[t++];this.targetObject.matrixWorldNeedsUpdate=!0}_setValue_arrayElement(e,t){this.resolvedProperty[this.propertyIndex]=e[t]}_setValue_arrayElement_setNeedsUpdate(e,t){this.resolvedProperty[this.propertyIndex]=e[t],this.targetObject.needsUpdate=!0}_setValue_arrayElement_setMatrixWorldNeedsUpdate(e,t){this.resolvedProperty[this.propertyIndex]=e[t],this.targetObject.matrixWorldNeedsUpdate=!0}_setValue_fromArray(e,t){this.resolvedProperty.fromArray(e,t)}_setValue_fromArray_setNeedsUpdate(e,t){this.resolvedProperty.fromArray(e,t),this.targetObject.needsUpdate=!0}_setValue_fromArray_setMatrixWorldNeedsUpdate(e,t){this.resolvedProperty.fromArray(e,t),this.targetObject.matrixWorldNeedsUpdate=!0}_getValue_unbound(e,t){this.bind(),this.getValue(e,t)}_setValue_unbound(e,t){this.bind(),this.setValue(e,t)}bind(){let e=this.node,t=this.parsedPath,n=t.objectName,r=t.propertyName,s=t.propertyIndex;if(e||(e=i.findNode(this.rootNode,t.nodeName),this.node=e),this.getValue=this._getValue_unavailable,this.setValue=this._setValue_unavailable,!e){console.warn("THREE.PropertyBinding: No target node found for track: "+this.path+".");return}if(n){let l=t.objectIndex;switch(n){case"materials":if(!e.material){console.error("THREE.PropertyBinding: Can not bind to material as node does not have a material.",this);return}if(!e.material.materials){console.error("THREE.PropertyBinding: Can not bind to material.materials as node.material does not have a materials array.",this);return}e=e.material.materials;break;case"bones":if(!e.skeleton){console.error("THREE.PropertyBinding: Can not bind to bones as node does not have a skeleton.",this);return}e=e.skeleton.bones;for(let u=0;u<e.length;u++)if(e[u].name===l){l=u;break}break;case"map":if("map"in e){e=e.map;break}if(!e.material){console.error("THREE.PropertyBinding: Can not bind to material as node does not have a material.",this);return}if(!e.material.map){console.error("THREE.PropertyBinding: Can not bind to material.map as node.material does not have a map.",this);return}e=e.material.map;break;default:if(e[n]===void 0){console.error("THREE.PropertyBinding: Can not bind to objectName of node undefined.",this);return}e=e[n]}if(l!==void 0){if(e[l]===void 0){console.error("THREE.PropertyBinding: Trying to bind to objectIndex of objectName, but is undefined.",this,e);return}e=e[l]}}let a=e[r];if(a===void 0){let l=t.nodeName;console.error("THREE.PropertyBinding: Trying to update property for track: "+l+"."+r+" but it wasn't found.",e);return}let o=this.Versioning.None;this.targetObject=e,e.isMaterial===!0?o=this.Versioning.NeedsUpdate:e.isObject3D===!0&&(o=this.Versioning.MatrixWorldNeedsUpdate);let c=this.BindingType.Direct;if(s!==void 0){if(r==="morphTargetInfluences"){if(!e.geometry){console.error("THREE.PropertyBinding: Can not bind to morphTargetInfluences because node does not have a geometry.",this);return}if(!e.geometry.morphAttributes){console.error("THREE.PropertyBinding: Can not bind to morphTargetInfluences because node does not have a geometry.morphAttributes.",this);return}e.morphTargetDictionary[s]!==void 0&&(s=e.morphTargetDictionary[s])}c=this.BindingType.ArrayElement,this.resolvedProperty=a,this.propertyIndex=s}else a.fromArray!==void 0&&a.toArray!==void 0?(c=this.BindingType.HasFromToArray,this.resolvedProperty=a):Array.isArray(a)?(c=this.BindingType.EntireArray,this.resolvedProperty=a):this.propertyName=r;this.getValue=this.GetterByBindingType[c],this.setValue=this.SetterByBindingTypeAndVersioning[c][o]}unbind(){this.node=null,this.getValue=this._getValue_unbound,this.setValue=this._setValue_unbound}};ct.Composite=Tl;ct.prototype.BindingType={Direct:0,EntireArray:1,ArrayElement:2,HasFromToArray:3};ct.prototype.Versioning={None:0,NeedsUpdate:1,MatrixWorldNeedsUpdate:2};ct.prototype.GetterByBindingType=[ct.prototype._getValue_direct,ct.prototype._getValue_array,ct.prototype._getValue_arrayElement,ct.prototype._getValue_toArray];ct.prototype.SetterByBindingTypeAndVersioning=[[ct.prototype._setValue_direct,ct.prototype._setValue_direct_setNeedsUpdate,ct.prototype._setValue_direct_setMatrixWorldNeedsUpdate],[ct.prototype._setValue_array,ct.prototype._setValue_array_setNeedsUpdate,ct.prototype._setValue_array_setMatrixWorldNeedsUpdate],[ct.prototype._setValue_arrayElement,ct.prototype._setValue_arrayElement_setNeedsUpdate,ct.prototype._setValue_arrayElement_setMatrixWorldNeedsUpdate],[ct.prototype._setValue_fromArray,ct.prototype._setValue_fromArray_setNeedsUpdate,ct.prototype._setValue_fromArray_setMatrixWorldNeedsUpdate]];var Dx=new Float32Array(1);var ds=class{constructor(e=1,t=0,n=0){this.radius=e,this.phi=t,this.theta=n}set(e,t,n){return this.radius=e,this.phi=t,this.theta=n,this}copy(e){return this.radius=e.radius,this.phi=e.phi,this.theta=e.theta,this}makeSafe(){return this.phi=Ye(this.phi,1e-6,Math.PI-1e-6),this}setFromVector3(e){return this.setFromCartesianCoords(e.x,e.y,e.z)}setFromCartesianCoords(e,t,n){return this.radius=Math.sqrt(e*e+t*t+n*n),this.radius===0?(this.theta=0,this.phi=0):(this.theta=Math.atan2(e,n),this.phi=Math.acos(Ye(t/this.radius,-1,1))),this}clone(){return new this.constructor().copy(this)}};var us=class extends ci{constructor(e=10,t=10,n=4473924,r=8947848){n=new Be(n),r=new Be(r);let s=t/2,a=e/t,o=e/2,c=[],l=[];for(let h=0,p=0,g=-o;h<=t;h++,g+=a){c.push(-o,0,g,o,0,g),c.push(g,0,-o,g,0,o);let x=h===s?n:r;x.toArray(l,p),p+=3,x.toArray(l,p),p+=3,x.toArray(l,p),p+=3,x.toArray(l,p),p+=3}let u=new ft;u.setAttribute("position",new nt(c,3)),u.setAttribute("color",new nt(l,3));let d=new nn({vertexColors:!0,toneMapped:!1});super(u,d),this.type="GridHelper"}dispose(){this.geometry.dispose(),this.material.dispose()}};var pd=new D,ra,_l,hs=class extends Mt{constructor(e=new D(0,0,1),t=new D(0,0,0),n=1,r=16776960,s=n*.2,a=s*.2){super(),this.type="ArrowHelper",ra===void 0&&(ra=new ft,ra.setAttribute("position",new nt([0,0,0,0,1,0],3)),_l=new xr(.5,1,5,1),_l.translate(0,-.5,0)),this.position.copy(t),this.line=new Xn(ra,new nn({color:r,toneMapped:!1})),this.line.matrixAutoUpdate=!1,this.add(this.line),this.cone=new dt(_l,new Wt({color:r,toneMapped:!1})),this.cone.matrixAutoUpdate=!1,this.add(this.cone),this.setDirection(e),this.setLength(n,s,a)}setDirection(e){if(e.y>.99999)this.quaternion.set(0,0,0,1);else if(e.y<-.99999)this.quaternion.set(1,0,0,0);else{pd.set(e.z,0,-e.x).normalize();let t=Math.acos(e.y);this.quaternion.setFromAxisAngle(pd,t)}}setLength(e,t=e*.2,n=t*.2){this.line.scale.set(1,Math.max(1e-4,e-t),1),this.line.updateMatrix(),this.cone.scale.set(n,t,n),this.cone.position.y=e,this.cone.updateMatrix()}setColor(e){this.line.material.color.set(e),this.cone.material.color.set(e)}copy(e){return super.copy(e,!1),this.line.copy(e.line),this.cone.copy(e.cone),this}dispose(){this.line.geometry.dispose(),this.line.material.dispose(),this.cone.geometry.dispose(),this.cone.material.dispose()}};function Jl(i,e,t,n){let r=wf(n);switch(t){case Bl:return i*e;case kl:return i*e/r.components*r.byteLength;case $a:return i*e/r.components*r.byteLength;case Hl:return i*e*2/r.components*r.byteLength;case qa:return i*e*2/r.components*r.byteLength;case zl:return i*e*3/r.components*r.byteLength;case hn:return i*e*4/r.components*r.byteLength;case Ya:return i*e*4/r.components*r.byteLength;case ms:case gs:return Math.floor((i+3)/4)*Math.floor((e+3)/4)*8;case xs:case _s:return Math.floor((i+3)/4)*Math.floor((e+3)/4)*16;case Ja:case ja:return Math.max(i,16)*Math.max(e,8)/4;case Za:case Ka:return Math.max(i,8)*Math.max(e,8)/2;case Qa:case eo:return Math.floor((i+3)/4)*Math.floor((e+3)/4)*8;case to:return Math.floor((i+3)/4)*Math.floor((e+3)/4)*16;case no:return Math.floor((i+3)/4)*Math.floor((e+3)/4)*16;case io:return Math.floor((i+4)/5)*Math.floor((e+3)/4)*16;case ro:return Math.floor((i+4)/5)*Math.floor((e+4)/5)*16;case so:return Math.floor((i+5)/6)*Math.floor((e+4)/5)*16;case ao:return Math.floor((i+5)/6)*Math.floor((e+5)/6)*16;case oo:return Math.floor((i+7)/8)*Math.floor((e+4)/5)*16;case lo:return Math.floor((i+7)/8)*Math.floor((e+5)/6)*16;case co:return Math.floor((i+7)/8)*Math.floor((e+7)/8)*16;case uo:return Math.floor((i+9)/10)*Math.floor((e+4)/5)*16;case ho:return Math.floor((i+9)/10)*Math.floor((e+5)/6)*16;case fo:return Math.floor((i+9)/10)*Math.floor((e+7)/8)*16;case po:return Math.floor((i+9)/10)*Math.floor((e+9)/10)*16;case mo:return Math.floor((i+11)/12)*Math.floor((e+9)/10)*16;case go:return Math.floor((i+11)/12)*Math.floor((e+11)/12)*16;case xo:case _o:case yo:return Math.ceil(i/4)*Math.ceil(e/4)*16;case vo:case bo:return Math.ceil(i/4)*Math.ceil(e/4)*8;case wo:case Mo:return Math.ceil(i/4)*Math.ceil(e/4)*16}throw new Error(`Unable to determine texture byte length for ${t} format.`)}function wf(i){switch(i){case Sn:case Ll:return{byteLength:1,components:1};case _r:case Fl:case yr:return{byteLength:2,components:1};case Wa:case Xa:return{byteLength:2,components:4};case pi:case Ga:case Nn:return{byteLength:4,components:1};case Ul:case Ol:return{byteLength:4,components:3}}throw new Error(`Unknown texture type ${i}.`)}typeof __THREE_DEVTOOLS__<"u"&&__THREE_DEVTOOLS__.dispatchEvent(new CustomEvent("register",{detail:{revision:"180"}}));typeof window<"u"&&(window.__THREE__?console.warn("WARNING: Multiple instances of Three.js being imported."):window.__THREE__="180");function Pu(){let i=null,e=!1,t=null,n=null;function r(s,a){t(s,a),n=i.requestAnimationFrame(r)}return{start:function(){e!==!0&&t!==null&&(n=i.requestAnimationFrame(r),e=!0)},stop:function(){i.cancelAnimationFrame(n),e=!1},setAnimationLoop:function(s){t=s},setContext:function(s){i=s}}}function Sf(i){let e=new WeakMap;function t(o,c){let l=o.array,u=o.usage,d=l.byteLength,h=i.createBuffer();i.bindBuffer(c,h),i.bufferData(c,l,u),o.onUploadCallback();let p;if(l instanceof Float32Array)p=i.FLOAT;else if(typeof Float16Array<"u"&&l instanceof Float16Array)p=i.HALF_FLOAT;else if(l instanceof Uint16Array)o.isFloat16BufferAttribute?p=i.HALF_FLOAT:p=i.UNSIGNED_SHORT;else if(l instanceof Int16Array)p=i.SHORT;else if(l instanceof Uint32Array)p=i.UNSIGNED_INT;else if(l instanceof Int32Array)p=i.INT;else if(l instanceof Int8Array)p=i.BYTE;else if(l instanceof Uint8Array)p=i.UNSIGNED_BYTE;else if(l instanceof Uint8ClampedArray)p=i.UNSIGNED_BYTE;else throw new Error("THREE.WebGLAttributes: Unsupported buffer data format: "+l);return{buffer:h,type:p,bytesPerElement:l.BYTES_PER_ELEMENT,version:o.version,size:d}}function n(o,c,l){let u=c.array,d=c.updateRanges;if(i.bindBuffer(l,o),d.length===0)i.bufferSubData(l,0,u);else{d.sort((p,g)=>p.start-g.start);let h=0;for(let p=1;p<d.length;p++){let g=d[h],x=d[p];x.start<=g.start+g.count+1?g.count=Math.max(g.count,x.start+x.count-g.start):(++h,d[h]=x)}d.length=h+1;for(let p=0,g=d.length;p<g;p++){let x=d[p];i.bufferSubData(l,x.start*u.BYTES_PER_ELEMENT,u,x.start,x.count)}c.clearUpdateRanges()}c.onUploadCallback()}function r(o){return o.isInterleavedBufferAttribute&&(o=o.data),e.get(o)}function s(o){o.isInterleavedBufferAttribute&&(o=o.data);let c=e.get(o);c&&(i.deleteBuffer(c.buffer),e.delete(o))}function a(o,c){if(o.isInterleavedBufferAttribute&&(o=o.data),o.isGLBufferAttribute){let u=e.get(o);(!u||u.version<o.version)&&e.set(o,{buffer:o.buffer,type:o.type,bytesPerElement:o.elementSize,version:o.version});return}let l=e.get(o);if(l===void 0)e.set(o,t(o,c));else if(l.version<o.version){if(l.size!==o.array.byteLength)throw new Error("THREE.WebGLAttributes: The size of the buffer attribute's array buffer does not match the original size. Resizing buffer attributes is not supported.");n(l.buffer,o,c),l.version=o.version}}return{get:r,remove:s,update:a}}var Ef=`#ifdef USE_ALPHAHASH
	if ( diffuseColor.a < getAlphaHashThreshold( vPosition ) ) discard;
#endif`,Tf=`#ifdef USE_ALPHAHASH
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
#endif`,Af=`#ifdef USE_ALPHAMAP
	diffuseColor.a *= texture2D( alphaMap, vAlphaMapUv ).g;
#endif`,Cf=`#ifdef USE_ALPHAMAP
	uniform sampler2D alphaMap;
#endif`,Rf=`#ifdef USE_ALPHATEST
	#ifdef ALPHA_TO_COVERAGE
	diffuseColor.a = smoothstep( alphaTest, alphaTest + fwidth( diffuseColor.a ), diffuseColor.a );
	if ( diffuseColor.a == 0.0 ) discard;
	#else
	if ( diffuseColor.a < alphaTest ) discard;
	#endif
#endif`,If=`#ifdef USE_ALPHATEST
	uniform float alphaTest;
#endif`,Pf=`#ifdef USE_AOMAP
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
#endif`,Nf=`#ifdef USE_AOMAP
	uniform sampler2D aoMap;
	uniform float aoMapIntensity;
#endif`,Df=`#ifdef USE_BATCHING
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
#endif`,Lf=`#ifdef USE_BATCHING
	mat4 batchingMatrix = getBatchingMatrix( getIndirectIndex( gl_DrawID ) );
#endif`,Ff=`vec3 transformed = vec3( position );
#ifdef USE_ALPHAHASH
	vPosition = vec3( position );
#endif`,Uf=`vec3 objectNormal = vec3( normal );
#ifdef USE_TANGENT
	vec3 objectTangent = vec3( tangent.xyz );
#endif`,Of=`float G_BlinnPhong_Implicit( ) {
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
} // validated`,Bf=`#ifdef USE_IRIDESCENCE
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
#endif`,zf=`#ifdef USE_BUMPMAP
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
#endif`,kf=`#if NUM_CLIPPING_PLANES > 0
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
#endif`,Hf=`#if NUM_CLIPPING_PLANES > 0
	varying vec3 vClipPosition;
	uniform vec4 clippingPlanes[ NUM_CLIPPING_PLANES ];
#endif`,Vf=`#if NUM_CLIPPING_PLANES > 0
	varying vec3 vClipPosition;
#endif`,Gf=`#if NUM_CLIPPING_PLANES > 0
	vClipPosition = - mvPosition.xyz;
#endif`,Wf=`#if defined( USE_COLOR_ALPHA )
	diffuseColor *= vColor;
#elif defined( USE_COLOR )
	diffuseColor.rgb *= vColor;
#endif`,Xf=`#if defined( USE_COLOR_ALPHA )
	varying vec4 vColor;
#elif defined( USE_COLOR )
	varying vec3 vColor;
#endif`,$f=`#if defined( USE_COLOR_ALPHA )
	varying vec4 vColor;
#elif defined( USE_COLOR ) || defined( USE_INSTANCING_COLOR ) || defined( USE_BATCHING_COLOR )
	varying vec3 vColor;
#endif`,qf=`#if defined( USE_COLOR_ALPHA )
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
#endif`,Yf=`#define PI 3.141592653589793
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
} // validated`,Zf=`#ifdef ENVMAP_TYPE_CUBE_UV
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
#endif`,Jf=`vec3 transformedNormal = objectNormal;
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
#endif`,Kf=`#ifdef USE_DISPLACEMENTMAP
	uniform sampler2D displacementMap;
	uniform float displacementScale;
	uniform float displacementBias;
#endif`,jf=`#ifdef USE_DISPLACEMENTMAP
	transformed += normalize( objectNormal ) * ( texture2D( displacementMap, vDisplacementMapUv ).x * displacementScale + displacementBias );
#endif`,Qf=`#ifdef USE_EMISSIVEMAP
	vec4 emissiveColor = texture2D( emissiveMap, vEmissiveMapUv );
	#ifdef DECODE_VIDEO_TEXTURE_EMISSIVE
		emissiveColor = sRGBTransferEOTF( emissiveColor );
	#endif
	totalEmissiveRadiance *= emissiveColor.rgb;
#endif`,ep=`#ifdef USE_EMISSIVEMAP
	uniform sampler2D emissiveMap;
#endif`,tp="gl_FragColor = linearToOutputTexel( gl_FragColor );",np=`vec4 LinearTransferOETF( in vec4 value ) {
	return value;
}
vec4 sRGBTransferEOTF( in vec4 value ) {
	return vec4( mix( pow( value.rgb * 0.9478672986 + vec3( 0.0521327014 ), vec3( 2.4 ) ), value.rgb * 0.0773993808, vec3( lessThanEqual( value.rgb, vec3( 0.04045 ) ) ) ), value.a );
}
vec4 sRGBTransferOETF( in vec4 value ) {
	return vec4( mix( pow( value.rgb, vec3( 0.41666 ) ) * 1.055 - vec3( 0.055 ), value.rgb * 12.92, vec3( lessThanEqual( value.rgb, vec3( 0.0031308 ) ) ) ), value.a );
}`,ip=`#ifdef USE_ENVMAP
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
#endif`,rp=`#ifdef USE_ENVMAP
	uniform float envMapIntensity;
	uniform float flipEnvMap;
	uniform mat3 envMapRotation;
	#ifdef ENVMAP_TYPE_CUBE
		uniform samplerCube envMap;
	#else
		uniform sampler2D envMap;
	#endif
	
#endif`,sp=`#ifdef USE_ENVMAP
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
#endif`,ap=`#ifdef USE_ENVMAP
	#if defined( USE_BUMPMAP ) || defined( USE_NORMALMAP ) || defined( PHONG ) || defined( LAMBERT )
		#define ENV_WORLDPOS
	#endif
	#ifdef ENV_WORLDPOS
		
		varying vec3 vWorldPosition;
	#else
		varying vec3 vReflect;
		uniform float refractionRatio;
	#endif
#endif`,op=`#ifdef USE_ENVMAP
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
#endif`,lp=`#ifdef USE_FOG
	vFogDepth = - mvPosition.z;
#endif`,cp=`#ifdef USE_FOG
	varying float vFogDepth;
#endif`,dp=`#ifdef USE_FOG
	#ifdef FOG_EXP2
		float fogFactor = 1.0 - exp( - fogDensity * fogDensity * vFogDepth * vFogDepth );
	#else
		float fogFactor = smoothstep( fogNear, fogFar, vFogDepth );
	#endif
	gl_FragColor.rgb = mix( gl_FragColor.rgb, fogColor, fogFactor );
#endif`,up=`#ifdef USE_FOG
	uniform vec3 fogColor;
	varying float vFogDepth;
	#ifdef FOG_EXP2
		uniform float fogDensity;
	#else
		uniform float fogNear;
		uniform float fogFar;
	#endif
#endif`,hp=`#ifdef USE_GRADIENTMAP
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
}`,fp=`#ifdef USE_LIGHTMAP
	uniform sampler2D lightMap;
	uniform float lightMapIntensity;
#endif`,pp=`LambertMaterial material;
material.diffuseColor = diffuseColor.rgb;
material.specularStrength = specularStrength;`,mp=`varying vec3 vViewPosition;
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
#define RE_IndirectDiffuse		RE_IndirectDiffuse_Lambert`,gp=`uniform bool receiveShadow;
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
#endif`,xp=`#ifdef USE_ENVMAP
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
#endif`,_p=`ToonMaterial material;
material.diffuseColor = diffuseColor.rgb;`,yp=`varying vec3 vViewPosition;
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
#define RE_IndirectDiffuse		RE_IndirectDiffuse_Toon`,vp=`BlinnPhongMaterial material;
material.diffuseColor = diffuseColor.rgb;
material.specularColor = specular;
material.specularShininess = shininess;
material.specularStrength = specularStrength;`,bp=`varying vec3 vViewPosition;
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
#define RE_IndirectDiffuse		RE_IndirectDiffuse_BlinnPhong`,wp=`PhysicalMaterial material;
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
#endif`,Mp=`struct PhysicalMaterial {
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
}`,Sp=`
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
#endif`,Ep=`#if defined( RE_IndirectDiffuse )
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
#endif`,Tp=`#if defined( RE_IndirectDiffuse )
	RE_IndirectDiffuse( irradiance, geometryPosition, geometryNormal, geometryViewDir, geometryClearcoatNormal, material, reflectedLight );
#endif
#if defined( RE_IndirectSpecular )
	RE_IndirectSpecular( radiance, iblIrradiance, clearcoatRadiance, geometryPosition, geometryNormal, geometryViewDir, geometryClearcoatNormal, material, reflectedLight );
#endif`,Ap=`#if defined( USE_LOGARITHMIC_DEPTH_BUFFER )
	gl_FragDepth = vIsPerspective == 0.0 ? gl_FragCoord.z : log2( vFragDepth ) * logDepthBufFC * 0.5;
#endif`,Cp=`#if defined( USE_LOGARITHMIC_DEPTH_BUFFER )
	uniform float logDepthBufFC;
	varying float vFragDepth;
	varying float vIsPerspective;
#endif`,Rp=`#ifdef USE_LOGARITHMIC_DEPTH_BUFFER
	varying float vFragDepth;
	varying float vIsPerspective;
#endif`,Ip=`#ifdef USE_LOGARITHMIC_DEPTH_BUFFER
	vFragDepth = 1.0 + gl_Position.w;
	vIsPerspective = float( isPerspectiveMatrix( projectionMatrix ) );
#endif`,Pp=`#ifdef USE_MAP
	vec4 sampledDiffuseColor = texture2D( map, vMapUv );
	#ifdef DECODE_VIDEO_TEXTURE
		sampledDiffuseColor = sRGBTransferEOTF( sampledDiffuseColor );
	#endif
	diffuseColor *= sampledDiffuseColor;
#endif`,Np=`#ifdef USE_MAP
	uniform sampler2D map;
#endif`,Dp=`#if defined( USE_MAP ) || defined( USE_ALPHAMAP )
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
#endif`,Lp=`#if defined( USE_POINTS_UV )
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
#endif`,Fp=`float metalnessFactor = metalness;
#ifdef USE_METALNESSMAP
	vec4 texelMetalness = texture2D( metalnessMap, vMetalnessMapUv );
	metalnessFactor *= texelMetalness.b;
#endif`,Up=`#ifdef USE_METALNESSMAP
	uniform sampler2D metalnessMap;
#endif`,Op=`#ifdef USE_INSTANCING_MORPH
	float morphTargetInfluences[ MORPHTARGETS_COUNT ];
	float morphTargetBaseInfluence = texelFetch( morphTexture, ivec2( 0, gl_InstanceID ), 0 ).r;
	for ( int i = 0; i < MORPHTARGETS_COUNT; i ++ ) {
		morphTargetInfluences[i] =  texelFetch( morphTexture, ivec2( i + 1, gl_InstanceID ), 0 ).r;
	}
#endif`,Bp=`#if defined( USE_MORPHCOLORS )
	vColor *= morphTargetBaseInfluence;
	for ( int i = 0; i < MORPHTARGETS_COUNT; i ++ ) {
		#if defined( USE_COLOR_ALPHA )
			if ( morphTargetInfluences[ i ] != 0.0 ) vColor += getMorph( gl_VertexID, i, 2 ) * morphTargetInfluences[ i ];
		#elif defined( USE_COLOR )
			if ( morphTargetInfluences[ i ] != 0.0 ) vColor += getMorph( gl_VertexID, i, 2 ).rgb * morphTargetInfluences[ i ];
		#endif
	}
#endif`,zp=`#ifdef USE_MORPHNORMALS
	objectNormal *= morphTargetBaseInfluence;
	for ( int i = 0; i < MORPHTARGETS_COUNT; i ++ ) {
		if ( morphTargetInfluences[ i ] != 0.0 ) objectNormal += getMorph( gl_VertexID, i, 1 ).xyz * morphTargetInfluences[ i ];
	}
#endif`,kp=`#ifdef USE_MORPHTARGETS
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
#endif`,Hp=`#ifdef USE_MORPHTARGETS
	transformed *= morphTargetBaseInfluence;
	for ( int i = 0; i < MORPHTARGETS_COUNT; i ++ ) {
		if ( morphTargetInfluences[ i ] != 0.0 ) transformed += getMorph( gl_VertexID, i, 0 ).xyz * morphTargetInfluences[ i ];
	}
#endif`,Vp=`float faceDirection = gl_FrontFacing ? 1.0 : - 1.0;
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
vec3 nonPerturbedNormal = normal;`,Gp=`#ifdef USE_NORMALMAP_OBJECTSPACE
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
#endif`,Wp=`#ifndef FLAT_SHADED
	varying vec3 vNormal;
	#ifdef USE_TANGENT
		varying vec3 vTangent;
		varying vec3 vBitangent;
	#endif
#endif`,Xp=`#ifndef FLAT_SHADED
	varying vec3 vNormal;
	#ifdef USE_TANGENT
		varying vec3 vTangent;
		varying vec3 vBitangent;
	#endif
#endif`,$p=`#ifndef FLAT_SHADED
	vNormal = normalize( transformedNormal );
	#ifdef USE_TANGENT
		vTangent = normalize( transformedTangent );
		vBitangent = normalize( cross( vNormal, vTangent ) * tangent.w );
	#endif
#endif`,qp=`#ifdef USE_NORMALMAP
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
#endif`,Yp=`#ifdef USE_CLEARCOAT
	vec3 clearcoatNormal = nonPerturbedNormal;
#endif`,Zp=`#ifdef USE_CLEARCOAT_NORMALMAP
	vec3 clearcoatMapN = texture2D( clearcoatNormalMap, vClearcoatNormalMapUv ).xyz * 2.0 - 1.0;
	clearcoatMapN.xy *= clearcoatNormalScale;
	clearcoatNormal = normalize( tbn2 * clearcoatMapN );
#endif`,Jp=`#ifdef USE_CLEARCOATMAP
	uniform sampler2D clearcoatMap;
#endif
#ifdef USE_CLEARCOAT_NORMALMAP
	uniform sampler2D clearcoatNormalMap;
	uniform vec2 clearcoatNormalScale;
#endif
#ifdef USE_CLEARCOAT_ROUGHNESSMAP
	uniform sampler2D clearcoatRoughnessMap;
#endif`,Kp=`#ifdef USE_IRIDESCENCEMAP
	uniform sampler2D iridescenceMap;
#endif
#ifdef USE_IRIDESCENCE_THICKNESSMAP
	uniform sampler2D iridescenceThicknessMap;
#endif`,jp=`#ifdef OPAQUE
diffuseColor.a = 1.0;
#endif
#ifdef USE_TRANSMISSION
diffuseColor.a *= material.transmissionAlpha;
#endif
gl_FragColor = vec4( outgoingLight, diffuseColor.a );`,Qp=`vec3 packNormalToRGB( const in vec3 normal ) {
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
}`,em=`#ifdef PREMULTIPLIED_ALPHA
	gl_FragColor.rgb *= gl_FragColor.a;
#endif`,tm=`vec4 mvPosition = vec4( transformed, 1.0 );
#ifdef USE_BATCHING
	mvPosition = batchingMatrix * mvPosition;
#endif
#ifdef USE_INSTANCING
	mvPosition = instanceMatrix * mvPosition;
#endif
mvPosition = modelViewMatrix * mvPosition;
gl_Position = projectionMatrix * mvPosition;`,nm=`#ifdef DITHERING
	gl_FragColor.rgb = dithering( gl_FragColor.rgb );
#endif`,im=`#ifdef DITHERING
	vec3 dithering( vec3 color ) {
		float grid_position = rand( gl_FragCoord.xy );
		vec3 dither_shift_RGB = vec3( 0.25 / 255.0, -0.25 / 255.0, 0.25 / 255.0 );
		dither_shift_RGB = mix( 2.0 * dither_shift_RGB, -2.0 * dither_shift_RGB, grid_position );
		return color + dither_shift_RGB;
	}
#endif`,rm=`float roughnessFactor = roughness;
#ifdef USE_ROUGHNESSMAP
	vec4 texelRoughness = texture2D( roughnessMap, vRoughnessMapUv );
	roughnessFactor *= texelRoughness.g;
#endif`,sm=`#ifdef USE_ROUGHNESSMAP
	uniform sampler2D roughnessMap;
#endif`,am=`#if NUM_SPOT_LIGHT_COORDS > 0
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
#endif`,om=`#if NUM_SPOT_LIGHT_COORDS > 0
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
#endif`,lm=`#if ( defined( USE_SHADOWMAP ) && ( NUM_DIR_LIGHT_SHADOWS > 0 || NUM_POINT_LIGHT_SHADOWS > 0 ) ) || ( NUM_SPOT_LIGHT_COORDS > 0 )
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
#endif`,cm=`float getShadowMask() {
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
}`,dm=`#ifdef USE_SKINNING
	mat4 boneMatX = getBoneMatrix( skinIndex.x );
	mat4 boneMatY = getBoneMatrix( skinIndex.y );
	mat4 boneMatZ = getBoneMatrix( skinIndex.z );
	mat4 boneMatW = getBoneMatrix( skinIndex.w );
#endif`,um=`#ifdef USE_SKINNING
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
#endif`,hm=`#ifdef USE_SKINNING
	vec4 skinVertex = bindMatrix * vec4( transformed, 1.0 );
	vec4 skinned = vec4( 0.0 );
	skinned += boneMatX * skinVertex * skinWeight.x;
	skinned += boneMatY * skinVertex * skinWeight.y;
	skinned += boneMatZ * skinVertex * skinWeight.z;
	skinned += boneMatW * skinVertex * skinWeight.w;
	transformed = ( bindMatrixInverse * skinned ).xyz;
#endif`,fm=`#ifdef USE_SKINNING
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
#endif`,pm=`float specularStrength;
#ifdef USE_SPECULARMAP
	vec4 texelSpecular = texture2D( specularMap, vSpecularMapUv );
	specularStrength = texelSpecular.r;
#else
	specularStrength = 1.0;
#endif`,mm=`#ifdef USE_SPECULARMAP
	uniform sampler2D specularMap;
#endif`,gm=`#if defined( TONE_MAPPING )
	gl_FragColor.rgb = toneMapping( gl_FragColor.rgb );
#endif`,xm=`#ifndef saturate
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
vec3 CustomToneMapping( vec3 color ) { return color; }`,_m=`#ifdef USE_TRANSMISSION
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
#endif`,ym=`#ifdef USE_TRANSMISSION
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
#endif`,vm=`#if defined( USE_UV ) || defined( USE_ANISOTROPY )
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
#endif`,bm=`#if defined( USE_UV ) || defined( USE_ANISOTROPY )
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
#endif`,wm=`#if defined( USE_UV ) || defined( USE_ANISOTROPY )
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
#endif`,Mm=`#if defined( USE_ENVMAP ) || defined( DISTANCE ) || defined ( USE_SHADOWMAP ) || defined ( USE_TRANSMISSION ) || NUM_SPOT_LIGHT_COORDS > 0
	vec4 worldPosition = vec4( transformed, 1.0 );
	#ifdef USE_BATCHING
		worldPosition = batchingMatrix * worldPosition;
	#endif
	#ifdef USE_INSTANCING
		worldPosition = instanceMatrix * worldPosition;
	#endif
	worldPosition = modelMatrix * worldPosition;
#endif`,Sm=`varying vec2 vUv;
uniform mat3 uvTransform;
void main() {
	vUv = ( uvTransform * vec3( uv, 1 ) ).xy;
	gl_Position = vec4( position.xy, 1.0, 1.0 );
}`,Em=`uniform sampler2D t2D;
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
}`,Tm=`varying vec3 vWorldDirection;
#include <common>
void main() {
	vWorldDirection = transformDirection( position, modelMatrix );
	#include <begin_vertex>
	#include <project_vertex>
	gl_Position.z = gl_Position.w;
}`,Am=`#ifdef ENVMAP_TYPE_CUBE
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
}`,Cm=`varying vec3 vWorldDirection;
#include <common>
void main() {
	vWorldDirection = transformDirection( position, modelMatrix );
	#include <begin_vertex>
	#include <project_vertex>
	gl_Position.z = gl_Position.w;
}`,Rm=`uniform samplerCube tCube;
uniform float tFlip;
uniform float opacity;
varying vec3 vWorldDirection;
void main() {
	vec4 texColor = textureCube( tCube, vec3( tFlip * vWorldDirection.x, vWorldDirection.yz ) );
	gl_FragColor = texColor;
	gl_FragColor.a *= opacity;
	#include <tonemapping_fragment>
	#include <colorspace_fragment>
}`,Im=`#include <common>
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
}`,Pm=`#if DEPTH_PACKING == 3200
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
}`,Nm=`#define DISTANCE
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
}`,Dm=`#define DISTANCE
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
}`,Lm=`varying vec3 vWorldDirection;
#include <common>
void main() {
	vWorldDirection = transformDirection( position, modelMatrix );
	#include <begin_vertex>
	#include <project_vertex>
}`,Fm=`uniform sampler2D tEquirect;
varying vec3 vWorldDirection;
#include <common>
void main() {
	vec3 direction = normalize( vWorldDirection );
	vec2 sampleUV = equirectUv( direction );
	gl_FragColor = texture2D( tEquirect, sampleUV );
	#include <tonemapping_fragment>
	#include <colorspace_fragment>
}`,Um=`uniform float scale;
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
}`,Om=`uniform vec3 diffuse;
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
}`,Bm=`#include <common>
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
}`,zm=`uniform vec3 diffuse;
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
}`,km=`#define LAMBERT
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
}`,Hm=`#define LAMBERT
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
}`,Vm=`#define MATCAP
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
}`,Gm=`#define MATCAP
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
}`,Wm=`#define NORMAL
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
}`,Xm=`#define NORMAL
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
}`,$m=`#define PHONG
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
}`,qm=`#define PHONG
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
}`,Ym=`#define STANDARD
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
}`,Zm=`#define STANDARD
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
}`,Jm=`#define TOON
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
}`,Km=`#define TOON
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
}`,jm=`uniform float size;
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
}`,Qm=`uniform vec3 diffuse;
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
}`,eg=`#include <common>
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
}`,tg=`uniform vec3 color;
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
}`,ng=`uniform float rotation;
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
}`,ig=`uniform vec3 diffuse;
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
}`,Xe={alphahash_fragment:Ef,alphahash_pars_fragment:Tf,alphamap_fragment:Af,alphamap_pars_fragment:Cf,alphatest_fragment:Rf,alphatest_pars_fragment:If,aomap_fragment:Pf,aomap_pars_fragment:Nf,batching_pars_vertex:Df,batching_vertex:Lf,begin_vertex:Ff,beginnormal_vertex:Uf,bsdfs:Of,iridescence_fragment:Bf,bumpmap_pars_fragment:zf,clipping_planes_fragment:kf,clipping_planes_pars_fragment:Hf,clipping_planes_pars_vertex:Vf,clipping_planes_vertex:Gf,color_fragment:Wf,color_pars_fragment:Xf,color_pars_vertex:$f,color_vertex:qf,common:Yf,cube_uv_reflection_fragment:Zf,defaultnormal_vertex:Jf,displacementmap_pars_vertex:Kf,displacementmap_vertex:jf,emissivemap_fragment:Qf,emissivemap_pars_fragment:ep,colorspace_fragment:tp,colorspace_pars_fragment:np,envmap_fragment:ip,envmap_common_pars_fragment:rp,envmap_pars_fragment:sp,envmap_pars_vertex:ap,envmap_physical_pars_fragment:xp,envmap_vertex:op,fog_vertex:lp,fog_pars_vertex:cp,fog_fragment:dp,fog_pars_fragment:up,gradientmap_pars_fragment:hp,lightmap_pars_fragment:fp,lights_lambert_fragment:pp,lights_lambert_pars_fragment:mp,lights_pars_begin:gp,lights_toon_fragment:_p,lights_toon_pars_fragment:yp,lights_phong_fragment:vp,lights_phong_pars_fragment:bp,lights_physical_fragment:wp,lights_physical_pars_fragment:Mp,lights_fragment_begin:Sp,lights_fragment_maps:Ep,lights_fragment_end:Tp,logdepthbuf_fragment:Ap,logdepthbuf_pars_fragment:Cp,logdepthbuf_pars_vertex:Rp,logdepthbuf_vertex:Ip,map_fragment:Pp,map_pars_fragment:Np,map_particle_fragment:Dp,map_particle_pars_fragment:Lp,metalnessmap_fragment:Fp,metalnessmap_pars_fragment:Up,morphinstance_vertex:Op,morphcolor_vertex:Bp,morphnormal_vertex:zp,morphtarget_pars_vertex:kp,morphtarget_vertex:Hp,normal_fragment_begin:Vp,normal_fragment_maps:Gp,normal_pars_fragment:Wp,normal_pars_vertex:Xp,normal_vertex:$p,normalmap_pars_fragment:qp,clearcoat_normal_fragment_begin:Yp,clearcoat_normal_fragment_maps:Zp,clearcoat_pars_fragment:Jp,iridescence_pars_fragment:Kp,opaque_fragment:jp,packing:Qp,premultiplied_alpha_fragment:em,project_vertex:tm,dithering_fragment:nm,dithering_pars_fragment:im,roughnessmap_fragment:rm,roughnessmap_pars_fragment:sm,shadowmap_pars_fragment:am,shadowmap_pars_vertex:om,shadowmap_vertex:lm,shadowmask_pars_fragment:cm,skinbase_vertex:dm,skinning_pars_vertex:um,skinning_vertex:hm,skinnormal_vertex:fm,specularmap_fragment:pm,specularmap_pars_fragment:mm,tonemapping_fragment:gm,tonemapping_pars_fragment:xm,transmission_fragment:_m,transmission_pars_fragment:ym,uv_pars_fragment:vm,uv_pars_vertex:bm,uv_vertex:wm,worldpos_vertex:Mm,background_vert:Sm,background_frag:Em,backgroundCube_vert:Tm,backgroundCube_frag:Am,cube_vert:Cm,cube_frag:Rm,depth_vert:Im,depth_frag:Pm,distanceRGBA_vert:Nm,distanceRGBA_frag:Dm,equirect_vert:Lm,equirect_frag:Fm,linedashed_vert:Um,linedashed_frag:Om,meshbasic_vert:Bm,meshbasic_frag:zm,meshlambert_vert:km,meshlambert_frag:Hm,meshmatcap_vert:Vm,meshmatcap_frag:Gm,meshnormal_vert:Wm,meshnormal_frag:Xm,meshphong_vert:$m,meshphong_frag:qm,meshphysical_vert:Ym,meshphysical_frag:Zm,meshtoon_vert:Jm,meshtoon_frag:Km,points_vert:jm,points_frag:Qm,shadow_vert:eg,shadow_frag:tg,sprite_vert:ng,sprite_frag:ig},ce={common:{diffuse:{value:new Be(16777215)},opacity:{value:1},map:{value:null},mapTransform:{value:new ke},alphaMap:{value:null},alphaMapTransform:{value:new ke},alphaTest:{value:0}},specularmap:{specularMap:{value:null},specularMapTransform:{value:new ke}},envmap:{envMap:{value:null},envMapRotation:{value:new ke},flipEnvMap:{value:-1},reflectivity:{value:1},ior:{value:1.5},refractionRatio:{value:.98}},aomap:{aoMap:{value:null},aoMapIntensity:{value:1},aoMapTransform:{value:new ke}},lightmap:{lightMap:{value:null},lightMapIntensity:{value:1},lightMapTransform:{value:new ke}},bumpmap:{bumpMap:{value:null},bumpMapTransform:{value:new ke},bumpScale:{value:1}},normalmap:{normalMap:{value:null},normalMapTransform:{value:new ke},normalScale:{value:new We(1,1)}},displacementmap:{displacementMap:{value:null},displacementMapTransform:{value:new ke},displacementScale:{value:1},displacementBias:{value:0}},emissivemap:{emissiveMap:{value:null},emissiveMapTransform:{value:new ke}},metalnessmap:{metalnessMap:{value:null},metalnessMapTransform:{value:new ke}},roughnessmap:{roughnessMap:{value:null},roughnessMapTransform:{value:new ke}},gradientmap:{gradientMap:{value:null}},fog:{fogDensity:{value:25e-5},fogNear:{value:1},fogFar:{value:2e3},fogColor:{value:new Be(16777215)}},lights:{ambientLightColor:{value:[]},lightProbe:{value:[]},directionalLights:{value:[],properties:{direction:{},color:{}}},directionalLightShadows:{value:[],properties:{shadowIntensity:1,shadowBias:{},shadowNormalBias:{},shadowRadius:{},shadowMapSize:{}}},directionalShadowMap:{value:[]},directionalShadowMatrix:{value:[]},spotLights:{value:[],properties:{color:{},position:{},direction:{},distance:{},coneCos:{},penumbraCos:{},decay:{}}},spotLightShadows:{value:[],properties:{shadowIntensity:1,shadowBias:{},shadowNormalBias:{},shadowRadius:{},shadowMapSize:{}}},spotLightMap:{value:[]},spotShadowMap:{value:[]},spotLightMatrix:{value:[]},pointLights:{value:[],properties:{color:{},position:{},decay:{},distance:{}}},pointLightShadows:{value:[],properties:{shadowIntensity:1,shadowBias:{},shadowNormalBias:{},shadowRadius:{},shadowMapSize:{},shadowCameraNear:{},shadowCameraFar:{}}},pointShadowMap:{value:[]},pointShadowMatrix:{value:[]},hemisphereLights:{value:[],properties:{direction:{},skyColor:{},groundColor:{}}},rectAreaLights:{value:[],properties:{color:{},position:{},width:{},height:{}}},ltc_1:{value:null},ltc_2:{value:null}},points:{diffuse:{value:new Be(16777215)},opacity:{value:1},size:{value:1},scale:{value:1},map:{value:null},alphaMap:{value:null},alphaMapTransform:{value:new ke},alphaTest:{value:0},uvTransform:{value:new ke}},sprite:{diffuse:{value:new Be(16777215)},opacity:{value:1},center:{value:new We(.5,.5)},rotation:{value:0},map:{value:null},mapTransform:{value:new ke},alphaMap:{value:null},alphaMapTransform:{value:new ke},alphaTest:{value:0}}},Dn={basic:{uniforms:Ft([ce.common,ce.specularmap,ce.envmap,ce.aomap,ce.lightmap,ce.fog]),vertexShader:Xe.meshbasic_vert,fragmentShader:Xe.meshbasic_frag},lambert:{uniforms:Ft([ce.common,ce.specularmap,ce.envmap,ce.aomap,ce.lightmap,ce.emissivemap,ce.bumpmap,ce.normalmap,ce.displacementmap,ce.fog,ce.lights,{emissive:{value:new Be(0)}}]),vertexShader:Xe.meshlambert_vert,fragmentShader:Xe.meshlambert_frag},phong:{uniforms:Ft([ce.common,ce.specularmap,ce.envmap,ce.aomap,ce.lightmap,ce.emissivemap,ce.bumpmap,ce.normalmap,ce.displacementmap,ce.fog,ce.lights,{emissive:{value:new Be(0)},specular:{value:new Be(1118481)},shininess:{value:30}}]),vertexShader:Xe.meshphong_vert,fragmentShader:Xe.meshphong_frag},standard:{uniforms:Ft([ce.common,ce.envmap,ce.aomap,ce.lightmap,ce.emissivemap,ce.bumpmap,ce.normalmap,ce.displacementmap,ce.roughnessmap,ce.metalnessmap,ce.fog,ce.lights,{emissive:{value:new Be(0)},roughness:{value:1},metalness:{value:0},envMapIntensity:{value:1}}]),vertexShader:Xe.meshphysical_vert,fragmentShader:Xe.meshphysical_frag},toon:{uniforms:Ft([ce.common,ce.aomap,ce.lightmap,ce.emissivemap,ce.bumpmap,ce.normalmap,ce.displacementmap,ce.gradientmap,ce.fog,ce.lights,{emissive:{value:new Be(0)}}]),vertexShader:Xe.meshtoon_vert,fragmentShader:Xe.meshtoon_frag},matcap:{uniforms:Ft([ce.common,ce.bumpmap,ce.normalmap,ce.displacementmap,ce.fog,{matcap:{value:null}}]),vertexShader:Xe.meshmatcap_vert,fragmentShader:Xe.meshmatcap_frag},points:{uniforms:Ft([ce.points,ce.fog]),vertexShader:Xe.points_vert,fragmentShader:Xe.points_frag},dashed:{uniforms:Ft([ce.common,ce.fog,{scale:{value:1},dashSize:{value:1},totalSize:{value:2}}]),vertexShader:Xe.linedashed_vert,fragmentShader:Xe.linedashed_frag},depth:{uniforms:Ft([ce.common,ce.displacementmap]),vertexShader:Xe.depth_vert,fragmentShader:Xe.depth_frag},normal:{uniforms:Ft([ce.common,ce.bumpmap,ce.normalmap,ce.displacementmap,{opacity:{value:1}}]),vertexShader:Xe.meshnormal_vert,fragmentShader:Xe.meshnormal_frag},sprite:{uniforms:Ft([ce.sprite,ce.fog]),vertexShader:Xe.sprite_vert,fragmentShader:Xe.sprite_frag},background:{uniforms:{uvTransform:{value:new ke},t2D:{value:null},backgroundIntensity:{value:1}},vertexShader:Xe.background_vert,fragmentShader:Xe.background_frag},backgroundCube:{uniforms:{envMap:{value:null},flipEnvMap:{value:-1},backgroundBlurriness:{value:0},backgroundIntensity:{value:1},backgroundRotation:{value:new ke}},vertexShader:Xe.backgroundCube_vert,fragmentShader:Xe.backgroundCube_frag},cube:{uniforms:{tCube:{value:null},tFlip:{value:-1},opacity:{value:1}},vertexShader:Xe.cube_vert,fragmentShader:Xe.cube_frag},equirect:{uniforms:{tEquirect:{value:null}},vertexShader:Xe.equirect_vert,fragmentShader:Xe.equirect_frag},distanceRGBA:{uniforms:Ft([ce.common,ce.displacementmap,{referencePosition:{value:new D},nearDistance:{value:1},farDistance:{value:1e3}}]),vertexShader:Xe.distanceRGBA_vert,fragmentShader:Xe.distanceRGBA_frag},shadow:{uniforms:Ft([ce.lights,ce.fog,{color:{value:new Be(0)},opacity:{value:1}}]),vertexShader:Xe.shadow_vert,fragmentShader:Xe.shadow_frag}};Dn.physical={uniforms:Ft([Dn.standard.uniforms,{clearcoat:{value:0},clearcoatMap:{value:null},clearcoatMapTransform:{value:new ke},clearcoatNormalMap:{value:null},clearcoatNormalMapTransform:{value:new ke},clearcoatNormalScale:{value:new We(1,1)},clearcoatRoughness:{value:0},clearcoatRoughnessMap:{value:null},clearcoatRoughnessMapTransform:{value:new ke},dispersion:{value:0},iridescence:{value:0},iridescenceMap:{value:null},iridescenceMapTransform:{value:new ke},iridescenceIOR:{value:1.3},iridescenceThicknessMinimum:{value:100},iridescenceThicknessMaximum:{value:400},iridescenceThicknessMap:{value:null},iridescenceThicknessMapTransform:{value:new ke},sheen:{value:0},sheenColor:{value:new Be(0)},sheenColorMap:{value:null},sheenColorMapTransform:{value:new ke},sheenRoughness:{value:1},sheenRoughnessMap:{value:null},sheenRoughnessMapTransform:{value:new ke},transmission:{value:0},transmissionMap:{value:null},transmissionMapTransform:{value:new ke},transmissionSamplerSize:{value:new We},transmissionSamplerMap:{value:null},thickness:{value:0},thicknessMap:{value:null},thicknessMapTransform:{value:new ke},attenuationDistance:{value:0},attenuationColor:{value:new Be(0)},specularColor:{value:new Be(1,1,1)},specularColorMap:{value:null},specularColorMapTransform:{value:new ke},specularIntensity:{value:1},specularIntensityMap:{value:null},specularIntensityMapTransform:{value:new ke},anisotropyVector:{value:new We},anisotropyMap:{value:null},anisotropyMapTransform:{value:new ke}}]),vertexShader:Xe.meshphysical_vert,fragmentShader:Xe.meshphysical_frag};var So={r:0,b:0,g:0},Ni=new en,rg=new ht;function sg(i,e,t,n,r,s,a){let o=new Be(0),c=s===!0?0:1,l,u,d=null,h=0,p=null;function g(M){let y=M.isScene===!0?M.background:null;return y&&y.isTexture&&(y=(M.backgroundBlurriness>0?t:e).get(y)),y}function x(M){let y=!1,C=g(M);C===null?f(o,c):C&&C.isColor&&(f(C,1),y=!0);let A=i.xr.getEnvironmentBlendMode();A==="additive"?n.buffers.color.setClear(0,0,0,1,a):A==="alpha-blend"&&n.buffers.color.setClear(0,0,0,0,a),(i.autoClear||y)&&(n.buffers.depth.setTest(!0),n.buffers.depth.setMask(!0),n.buffers.color.setMask(!0),i.clear(i.autoClearColor,i.autoClearDepth,i.autoClearStencil))}function m(M,y){let C=g(y);C&&(C.isCubeTexture||C.mapping===fs)?(u===void 0&&(u=new dt(new Mn(1,1,1),new tn({name:"BackgroundCubeMaterial",uniforms:Pi(Dn.backgroundCube.uniforms),vertexShader:Dn.backgroundCube.vertexShader,fragmentShader:Dn.backgroundCube.fragmentShader,side:zt,depthTest:!1,depthWrite:!1,fog:!1,allowOverride:!1})),u.geometry.deleteAttribute("normal"),u.geometry.deleteAttribute("uv"),u.onBeforeRender=function(A,I,N){this.matrixWorld.copyPosition(N.matrixWorld)},Object.defineProperty(u.material,"envMap",{get:function(){return this.uniforms.envMap.value}}),r.update(u)),Ni.copy(y.backgroundRotation),Ni.x*=-1,Ni.y*=-1,Ni.z*=-1,C.isCubeTexture&&C.isRenderTargetTexture===!1&&(Ni.y*=-1,Ni.z*=-1),u.material.uniforms.envMap.value=C,u.material.uniforms.flipEnvMap.value=C.isCubeTexture&&C.isRenderTargetTexture===!1?-1:1,u.material.uniforms.backgroundBlurriness.value=y.backgroundBlurriness,u.material.uniforms.backgroundIntensity.value=y.backgroundIntensity,u.material.uniforms.backgroundRotation.value.setFromMatrix4(rg.makeRotationFromEuler(Ni)),u.material.toneMapped=Ke.getTransfer(C.colorSpace)!==tt,(d!==C||h!==C.version||p!==i.toneMapping)&&(u.material.needsUpdate=!0,d=C,h=C.version,p=i.toneMapping),u.layers.enableAll(),M.unshift(u,u.geometry,u.material,0,0,null)):C&&C.isTexture&&(l===void 0&&(l=new dt(new Ai(2,2),new tn({name:"BackgroundMaterial",uniforms:Pi(Dn.background.uniforms),vertexShader:Dn.background.vertexShader,fragmentShader:Dn.background.fragmentShader,side:Gn,depthTest:!1,depthWrite:!1,fog:!1,allowOverride:!1})),l.geometry.deleteAttribute("normal"),Object.defineProperty(l.material,"map",{get:function(){return this.uniforms.t2D.value}}),r.update(l)),l.material.uniforms.t2D.value=C,l.material.uniforms.backgroundIntensity.value=y.backgroundIntensity,l.material.toneMapped=Ke.getTransfer(C.colorSpace)!==tt,C.matrixAutoUpdate===!0&&C.updateMatrix(),l.material.uniforms.uvTransform.value.copy(C.matrix),(d!==C||h!==C.version||p!==i.toneMapping)&&(l.material.needsUpdate=!0,d=C,h=C.version,p=i.toneMapping),l.layers.enableAll(),M.unshift(l,l.geometry,l.material,0,0,null))}function f(M,y){M.getRGB(So,ql(i)),n.buffers.color.setClear(So.r,So.g,So.b,y,a)}function S(){u!==void 0&&(u.geometry.dispose(),u.material.dispose(),u=void 0),l!==void 0&&(l.geometry.dispose(),l.material.dispose(),l=void 0)}return{getClearColor:function(){return o},setClearColor:function(M,y=1){o.set(M),c=y,f(o,c)},getClearAlpha:function(){return c},setClearAlpha:function(M){c=M,f(o,c)},render:x,addToRenderList:m,dispose:S}}function ag(i,e){let t=i.getParameter(i.MAX_VERTEX_ATTRIBS),n={},r=h(null),s=r,a=!1;function o(b,T,P,U,F){let k=!1,G=d(U,P,T);s!==G&&(s=G,l(s.object)),k=p(b,U,P,F),k&&g(b,U,P,F),F!==null&&e.update(F,i.ELEMENT_ARRAY_BUFFER),(k||a)&&(a=!1,y(b,T,P,U),F!==null&&i.bindBuffer(i.ELEMENT_ARRAY_BUFFER,e.get(F).buffer))}function c(){return i.createVertexArray()}function l(b){return i.bindVertexArray(b)}function u(b){return i.deleteVertexArray(b)}function d(b,T,P){let U=P.wireframe===!0,F=n[b.id];F===void 0&&(F={},n[b.id]=F);let k=F[T.id];k===void 0&&(k={},F[T.id]=k);let G=k[U];return G===void 0&&(G=h(c()),k[U]=G),G}function h(b){let T=[],P=[],U=[];for(let F=0;F<t;F++)T[F]=0,P[F]=0,U[F]=0;return{geometry:null,program:null,wireframe:!1,newAttributes:T,enabledAttributes:P,attributeDivisors:U,object:b,attributes:{},index:null}}function p(b,T,P,U){let F=s.attributes,k=T.attributes,G=0,K=P.getAttributes();for(let W in K)if(K[W].location>=0){let de=F[W],Ae=k[W];if(Ae===void 0&&(W==="instanceMatrix"&&b.instanceMatrix&&(Ae=b.instanceMatrix),W==="instanceColor"&&b.instanceColor&&(Ae=b.instanceColor)),de===void 0||de.attribute!==Ae||Ae&&de.data!==Ae.data)return!0;G++}return s.attributesNum!==G||s.index!==U}function g(b,T,P,U){let F={},k=T.attributes,G=0,K=P.getAttributes();for(let W in K)if(K[W].location>=0){let de=k[W];de===void 0&&(W==="instanceMatrix"&&b.instanceMatrix&&(de=b.instanceMatrix),W==="instanceColor"&&b.instanceColor&&(de=b.instanceColor));let Ae={};Ae.attribute=de,de&&de.data&&(Ae.data=de.data),F[W]=Ae,G++}s.attributes=F,s.attributesNum=G,s.index=U}function x(){let b=s.newAttributes;for(let T=0,P=b.length;T<P;T++)b[T]=0}function m(b){f(b,0)}function f(b,T){let P=s.newAttributes,U=s.enabledAttributes,F=s.attributeDivisors;P[b]=1,U[b]===0&&(i.enableVertexAttribArray(b),U[b]=1),F[b]!==T&&(i.vertexAttribDivisor(b,T),F[b]=T)}function S(){let b=s.newAttributes,T=s.enabledAttributes;for(let P=0,U=T.length;P<U;P++)T[P]!==b[P]&&(i.disableVertexAttribArray(P),T[P]=0)}function M(b,T,P,U,F,k,G){G===!0?i.vertexAttribIPointer(b,T,P,F,k):i.vertexAttribPointer(b,T,P,U,F,k)}function y(b,T,P,U){x();let F=U.attributes,k=P.getAttributes(),G=T.defaultAttributeValues;for(let K in k){let W=k[K];if(W.location>=0){let se=F[K];if(se===void 0&&(K==="instanceMatrix"&&b.instanceMatrix&&(se=b.instanceMatrix),K==="instanceColor"&&b.instanceColor&&(se=b.instanceColor)),se!==void 0){let de=se.normalized,Ae=se.itemSize,fe=e.get(se);if(fe===void 0)continue;let Oe=fe.buffer,$e=fe.type,Pe=fe.bytesPerElement,X=$e===i.INT||$e===i.UNSIGNED_INT||se.gpuType===Ga;if(se.isInterleavedBufferAttribute){let J=se.data,Y=J.stride,ae=se.offset;if(J.isInstancedInterleavedBuffer){for(let pe=0;pe<W.locationSize;pe++)f(W.location+pe,J.meshPerAttribute);b.isInstancedMesh!==!0&&U._maxInstanceCount===void 0&&(U._maxInstanceCount=J.meshPerAttribute*J.count)}else for(let pe=0;pe<W.locationSize;pe++)m(W.location+pe);i.bindBuffer(i.ARRAY_BUFFER,Oe);for(let pe=0;pe<W.locationSize;pe++)M(W.location+pe,Ae/W.locationSize,$e,de,Y*Pe,(ae+Ae/W.locationSize*pe)*Pe,X)}else{if(se.isInstancedBufferAttribute){for(let J=0;J<W.locationSize;J++)f(W.location+J,se.meshPerAttribute);b.isInstancedMesh!==!0&&U._maxInstanceCount===void 0&&(U._maxInstanceCount=se.meshPerAttribute*se.count)}else for(let J=0;J<W.locationSize;J++)m(W.location+J);i.bindBuffer(i.ARRAY_BUFFER,Oe);for(let J=0;J<W.locationSize;J++)M(W.location+J,Ae/W.locationSize,$e,de,Ae*Pe,Ae/W.locationSize*J*Pe,X)}}else if(G!==void 0){let de=G[K];if(de!==void 0)switch(de.length){case 2:i.vertexAttrib2fv(W.location,de);break;case 3:i.vertexAttrib3fv(W.location,de);break;case 4:i.vertexAttrib4fv(W.location,de);break;default:i.vertexAttrib1fv(W.location,de)}}}}S()}function C(){N();for(let b in n){let T=n[b];for(let P in T){let U=T[P];for(let F in U)u(U[F].object),delete U[F];delete T[P]}delete n[b]}}function A(b){if(n[b.id]===void 0)return;let T=n[b.id];for(let P in T){let U=T[P];for(let F in U)u(U[F].object),delete U[F];delete T[P]}delete n[b.id]}function I(b){for(let T in n){let P=n[T];if(P[b.id]===void 0)continue;let U=P[b.id];for(let F in U)u(U[F].object),delete U[F];delete P[b.id]}}function N(){v(),a=!0,s!==r&&(s=r,l(s.object))}function v(){r.geometry=null,r.program=null,r.wireframe=!1}return{setup:o,reset:N,resetDefaultState:v,dispose:C,releaseStatesOfGeometry:A,releaseStatesOfProgram:I,initAttributes:x,enableAttribute:m,disableUnusedAttributes:S}}function og(i,e,t){let n;function r(l){n=l}function s(l,u){i.drawArrays(n,l,u),t.update(u,n,1)}function a(l,u,d){d!==0&&(i.drawArraysInstanced(n,l,u,d),t.update(u,n,d))}function o(l,u,d){if(d===0)return;e.get("WEBGL_multi_draw").multiDrawArraysWEBGL(n,l,0,u,0,d);let p=0;for(let g=0;g<d;g++)p+=u[g];t.update(p,n,1)}function c(l,u,d,h){if(d===0)return;let p=e.get("WEBGL_multi_draw");if(p===null)for(let g=0;g<l.length;g++)a(l[g],u[g],h[g]);else{p.multiDrawArraysInstancedWEBGL(n,l,0,u,0,h,0,d);let g=0;for(let x=0;x<d;x++)g+=u[x]*h[x];t.update(g,n,1)}}this.setMode=r,this.render=s,this.renderInstances=a,this.renderMultiDraw=o,this.renderMultiDrawInstances=c}function lg(i,e,t,n){let r;function s(){if(r!==void 0)return r;if(e.has("EXT_texture_filter_anisotropic")===!0){let I=e.get("EXT_texture_filter_anisotropic");r=i.getParameter(I.MAX_TEXTURE_MAX_ANISOTROPY_EXT)}else r=0;return r}function a(I){return!(I!==hn&&n.convert(I)!==i.getParameter(i.IMPLEMENTATION_COLOR_READ_FORMAT))}function o(I){let N=I===yr&&(e.has("EXT_color_buffer_half_float")||e.has("EXT_color_buffer_float"));return!(I!==Sn&&n.convert(I)!==i.getParameter(i.IMPLEMENTATION_COLOR_READ_TYPE)&&I!==Nn&&!N)}function c(I){if(I==="highp"){if(i.getShaderPrecisionFormat(i.VERTEX_SHADER,i.HIGH_FLOAT).precision>0&&i.getShaderPrecisionFormat(i.FRAGMENT_SHADER,i.HIGH_FLOAT).precision>0)return"highp";I="mediump"}return I==="mediump"&&i.getShaderPrecisionFormat(i.VERTEX_SHADER,i.MEDIUM_FLOAT).precision>0&&i.getShaderPrecisionFormat(i.FRAGMENT_SHADER,i.MEDIUM_FLOAT).precision>0?"mediump":"lowp"}let l=t.precision!==void 0?t.precision:"highp",u=c(l);u!==l&&(console.warn("THREE.WebGLRenderer:",l,"not supported, using",u,"instead."),l=u);let d=t.logarithmicDepthBuffer===!0,h=t.reversedDepthBuffer===!0&&e.has("EXT_clip_control"),p=i.getParameter(i.MAX_TEXTURE_IMAGE_UNITS),g=i.getParameter(i.MAX_VERTEX_TEXTURE_IMAGE_UNITS),x=i.getParameter(i.MAX_TEXTURE_SIZE),m=i.getParameter(i.MAX_CUBE_MAP_TEXTURE_SIZE),f=i.getParameter(i.MAX_VERTEX_ATTRIBS),S=i.getParameter(i.MAX_VERTEX_UNIFORM_VECTORS),M=i.getParameter(i.MAX_VARYING_VECTORS),y=i.getParameter(i.MAX_FRAGMENT_UNIFORM_VECTORS),C=g>0,A=i.getParameter(i.MAX_SAMPLES);return{isWebGL2:!0,getMaxAnisotropy:s,getMaxPrecision:c,textureFormatReadable:a,textureTypeReadable:o,precision:l,logarithmicDepthBuffer:d,reversedDepthBuffer:h,maxTextures:p,maxVertexTextures:g,maxTextureSize:x,maxCubemapSize:m,maxAttributes:f,maxVertexUniforms:S,maxVaryings:M,maxFragmentUniforms:y,vertexTextures:C,maxSamples:A}}function cg(i){let e=this,t=null,n=0,r=!1,s=!1,a=new An,o=new ke,c={value:null,needsUpdate:!1};this.uniform=c,this.numPlanes=0,this.numIntersection=0,this.init=function(d,h){let p=d.length!==0||h||n!==0||r;return r=h,n=d.length,p},this.beginShadows=function(){s=!0,u(null)},this.endShadows=function(){s=!1},this.setGlobalState=function(d,h){t=u(d,h,0)},this.setState=function(d,h,p){let g=d.clippingPlanes,x=d.clipIntersection,m=d.clipShadows,f=i.get(d);if(!r||g===null||g.length===0||s&&!m)s?u(null):l();else{let S=s?0:n,M=S*4,y=f.clippingState||null;c.value=y,y=u(g,h,M,p);for(let C=0;C!==M;++C)y[C]=t[C];f.clippingState=y,this.numIntersection=x?this.numPlanes:0,this.numPlanes+=S}};function l(){c.value!==t&&(c.value=t,c.needsUpdate=n>0),e.numPlanes=n,e.numIntersection=0}function u(d,h,p,g){let x=d!==null?d.length:0,m=null;if(x!==0){if(m=c.value,g!==!0||m===null){let f=p+x*4,S=h.matrixWorldInverse;o.getNormalMatrix(S),(m===null||m.length<f)&&(m=new Float32Array(f));for(let M=0,y=p;M!==x;++M,y+=4)a.copy(d[M]).applyMatrix4(S,o),a.normal.toArray(m,y),m[y+3]=a.constant}c.value=m,c.needsUpdate=!0}return e.numPlanes=x,e.numIntersection=0,m}}function dg(i){let e=new WeakMap;function t(a,o){return o===ka?a.mapping=Ri:o===Ha&&(a.mapping=Ii),a}function n(a){if(a&&a.isTexture){let o=a.mapping;if(o===ka||o===Ha)if(e.has(a)){let c=e.get(a).texture;return t(c,a.mapping)}else{let c=a.image;if(c&&c.height>0){let l=new ga(c.height);return l.fromEquirectangularTexture(i,a),e.set(a,l),a.addEventListener("dispose",r),t(l.texture,a.mapping)}else return null}}return a}function r(a){let o=a.target;o.removeEventListener("dispose",r);let c=e.get(o);c!==void 0&&(e.delete(o),c.dispose())}function s(){e=new WeakMap}return{get:n,dispose:s}}var Mr=4,lu=[.125,.215,.35,.446,.526,.582],Fi=20,Kl=new ls,cu=new Be,jl=null,Ql=0,ec=0,tc=!1,Li=(1+Math.sqrt(5))/2,wr=1/Li,du=[new D(-Li,wr,0),new D(Li,wr,0),new D(-wr,0,Li),new D(wr,0,Li),new D(0,Li,-wr),new D(0,Li,wr),new D(-1,1,-1),new D(1,1,-1),new D(-1,1,1),new D(1,1,1)],ug=new D,Ao=class{constructor(e){this._renderer=e,this._pingPongRenderTarget=null,this._lodMax=0,this._cubeSize=0,this._lodPlanes=[],this._sizeLods=[],this._sigmas=[],this._blurMaterial=null,this._cubemapMaterial=null,this._equirectMaterial=null,this._compileMaterial(this._blurMaterial)}fromScene(e,t=0,n=.1,r=100,s={}){let{size:a=256,position:o=ug}=s;jl=this._renderer.getRenderTarget(),Ql=this._renderer.getActiveCubeFace(),ec=this._renderer.getActiveMipmapLevel(),tc=this._renderer.xr.enabled,this._renderer.xr.enabled=!1,this._setSize(a);let c=this._allocateTargets();return c.depthBuffer=!0,this._sceneToCubeUV(e,n,r,c,o),t>0&&this._blur(c,0,0,t),this._applyPMREM(c),this._cleanup(c),c}fromEquirectangular(e,t=null){return this._fromTexture(e,t)}fromCubemap(e,t=null){return this._fromTexture(e,t)}compileCubemapShader(){this._cubemapMaterial===null&&(this._cubemapMaterial=fu(),this._compileMaterial(this._cubemapMaterial))}compileEquirectangularShader(){this._equirectMaterial===null&&(this._equirectMaterial=hu(),this._compileMaterial(this._equirectMaterial))}dispose(){this._dispose(),this._cubemapMaterial!==null&&this._cubemapMaterial.dispose(),this._equirectMaterial!==null&&this._equirectMaterial.dispose()}_setSize(e){this._lodMax=Math.floor(Math.log2(e)),this._cubeSize=Math.pow(2,this._lodMax)}_dispose(){this._blurMaterial!==null&&this._blurMaterial.dispose(),this._pingPongRenderTarget!==null&&this._pingPongRenderTarget.dispose();for(let e=0;e<this._lodPlanes.length;e++)this._lodPlanes[e].dispose()}_cleanup(e){this._renderer.setRenderTarget(jl,Ql,ec),this._renderer.xr.enabled=tc,e.scissorTest=!1,Eo(e,0,0,e.width,e.height)}_fromTexture(e,t){e.mapping===Ri||e.mapping===Ii?this._setSize(e.image.length===0?16:e.image[0].width||e.image[0].image.width):this._setSize(e.image.width/4),jl=this._renderer.getRenderTarget(),Ql=this._renderer.getActiveCubeFace(),ec=this._renderer.getActiveMipmapLevel(),tc=this._renderer.xr.enabled,this._renderer.xr.enabled=!1;let n=t||this._allocateTargets();return this._textureToCubeUV(e,n),this._applyPMREM(n),this._cleanup(n),n}_allocateTargets(){let e=3*Math.max(this._cubeSize,112),t=4*this._cubeSize,n={magFilter:bn,minFilter:bn,generateMipmaps:!1,type:yr,format:hn,colorSpace:Ti,depthBuffer:!1},r=uu(e,t,n);if(this._pingPongRenderTarget===null||this._pingPongRenderTarget.width!==e||this._pingPongRenderTarget.height!==t){this._pingPongRenderTarget!==null&&this._dispose(),this._pingPongRenderTarget=uu(e,t,n);let{_lodMax:s}=this;({sizeLods:this._sizeLods,lodPlanes:this._lodPlanes,sigmas:this._sigmas}=hg(s)),this._blurMaterial=fg(s,e,t)}return r}_compileMaterial(e){let t=new dt(this._lodPlanes[0],e);this._renderer.compile(t,Kl)}_sceneToCubeUV(e,t,n,r,s){let c=new Dt(90,1,t,n),l=[1,-1,1,1,1,1],u=[1,1,1,-1,-1,-1],d=this._renderer,h=d.autoClear,p=d.toneMapping;d.getClearColor(cu),d.toneMapping=qn,d.autoClear=!1,d.state.buffers.depth.getReversed()&&(d.setRenderTarget(r),d.clearDepth(),d.setRenderTarget(null));let x=new Wt({name:"PMREM.Background",side:zt,depthWrite:!1,depthTest:!1}),m=new dt(new Mn,x),f=!1,S=e.background;S?S.isColor&&(x.color.copy(S),e.background=null,f=!0):(x.color.copy(cu),f=!0);for(let M=0;M<6;M++){let y=M%3;y===0?(c.up.set(0,l[M],0),c.position.set(s.x,s.y,s.z),c.lookAt(s.x+u[M],s.y,s.z)):y===1?(c.up.set(0,0,l[M]),c.position.set(s.x,s.y,s.z),c.lookAt(s.x,s.y+u[M],s.z)):(c.up.set(0,l[M],0),c.position.set(s.x,s.y,s.z),c.lookAt(s.x,s.y,s.z+u[M]));let C=this._cubeSize;Eo(r,y*C,M>2?C:0,C,C),d.setRenderTarget(r),f&&d.render(m,c),d.render(e,c)}m.geometry.dispose(),m.material.dispose(),d.toneMapping=p,d.autoClear=h,e.background=S}_textureToCubeUV(e,t){let n=this._renderer,r=e.mapping===Ri||e.mapping===Ii;r?(this._cubemapMaterial===null&&(this._cubemapMaterial=fu()),this._cubemapMaterial.uniforms.flipEnvMap.value=e.isRenderTargetTexture===!1?-1:1):this._equirectMaterial===null&&(this._equirectMaterial=hu());let s=r?this._cubemapMaterial:this._equirectMaterial,a=new dt(this._lodPlanes[0],s),o=s.uniforms;o.envMap.value=e;let c=this._cubeSize;Eo(t,0,0,3*c,2*c),n.setRenderTarget(t),n.render(a,Kl)}_applyPMREM(e){let t=this._renderer,n=t.autoClear;t.autoClear=!1;let r=this._lodPlanes.length;for(let s=1;s<r;s++){let a=Math.sqrt(this._sigmas[s]*this._sigmas[s]-this._sigmas[s-1]*this._sigmas[s-1]),o=du[(r-s-1)%du.length];this._blur(e,s-1,s,a,o)}t.autoClear=n}_blur(e,t,n,r,s){let a=this._pingPongRenderTarget;this._halfBlur(e,a,t,n,r,"latitudinal",s),this._halfBlur(a,e,n,n,r,"longitudinal",s)}_halfBlur(e,t,n,r,s,a,o){let c=this._renderer,l=this._blurMaterial;a!=="latitudinal"&&a!=="longitudinal"&&console.error("blur direction must be either latitudinal or longitudinal!");let u=3,d=new dt(this._lodPlanes[r],l),h=l.uniforms,p=this._sizeLods[n]-1,g=isFinite(s)?Math.PI/(2*p):2*Math.PI/(2*Fi-1),x=s/g,m=isFinite(s)?1+Math.floor(u*x):Fi;m>Fi&&console.warn(`sigmaRadians, ${s}, is too large and will clip, as it requested ${m} samples when the maximum is set to ${Fi}`);let f=[],S=0;for(let I=0;I<Fi;++I){let N=I/x,v=Math.exp(-N*N/2);f.push(v),I===0?S+=v:I<m&&(S+=2*v)}for(let I=0;I<f.length;I++)f[I]=f[I]/S;h.envMap.value=e.texture,h.samples.value=m,h.weights.value=f,h.latitudinal.value=a==="latitudinal",o&&(h.poleAxis.value=o);let{_lodMax:M}=this;h.dTheta.value=g,h.mipInt.value=M-n;let y=this._sizeLods[r],C=3*y*(r>M-Mr?r-M+Mr:0),A=4*(this._cubeSize-y);Eo(t,C,A,3*y,2*y),c.setRenderTarget(t),c.render(d,Kl)}};function hg(i){let e=[],t=[],n=[],r=i,s=i-Mr+1+lu.length;for(let a=0;a<s;a++){let o=Math.pow(2,r);t.push(o);let c=1/o;a>i-Mr?c=lu[a-i+Mr-1]:a===0&&(c=0),n.push(c);let l=1/(o-2),u=-l,d=1+l,h=[u,u,d,u,d,d,u,u,d,d,u,d],p=6,g=6,x=3,m=2,f=1,S=new Float32Array(x*g*p),M=new Float32Array(m*g*p),y=new Float32Array(f*g*p);for(let A=0;A<p;A++){let I=A%3*2/3-1,N=A>2?0:-1,v=[I,N,0,I+2/3,N,0,I+2/3,N+1,0,I,N,0,I+2/3,N+1,0,I,N+1,0];S.set(v,x*g*A),M.set(h,m*g*A);let b=[A,A,A,A,A,A];y.set(b,f*g*A)}let C=new ft;C.setAttribute("position",new Vt(S,x)),C.setAttribute("uv",new Vt(M,m)),C.setAttribute("faceIndex",new Vt(y,f)),e.push(C),r>Mr&&r--}return{lodPlanes:e,sizeLods:t,sigmas:n}}function uu(i,e,t){let n=new Rn(i,e,t);return n.texture.mapping=fs,n.texture.name="PMREM.cubeUv",n.scissorTest=!0,n}function Eo(i,e,t,n,r){i.viewport.set(e,t,n,r),i.scissor.set(e,t,n,r)}function fg(i,e,t){let n=new Float32Array(Fi),r=new D(0,1,0);return new tn({name:"SphericalGaussianBlur",defines:{n:Fi,CUBEUV_TEXEL_WIDTH:1/e,CUBEUV_TEXEL_HEIGHT:1/t,CUBEUV_MAX_MIP:`${i}.0`},uniforms:{envMap:{value:null},samples:{value:1},weights:{value:n},latitudinal:{value:!1},dTheta:{value:0},mipInt:{value:0},poleAxis:{value:r}},vertexShader:uc(),fragmentShader:`

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
		`,blending:$n,depthTest:!1,depthWrite:!1})}function hu(){return new tn({name:"EquirectangularToCubeUV",uniforms:{envMap:{value:null}},vertexShader:uc(),fragmentShader:`

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
		`,blending:$n,depthTest:!1,depthWrite:!1})}function fu(){return new tn({name:"CubemapToCubeUV",uniforms:{envMap:{value:null},flipEnvMap:{value:-1}},vertexShader:uc(),fragmentShader:`

			precision mediump float;
			precision mediump int;

			uniform float flipEnvMap;

			varying vec3 vOutputDirection;

			uniform samplerCube envMap;

			void main() {

				gl_FragColor = textureCube( envMap, vec3( flipEnvMap * vOutputDirection.x, vOutputDirection.yz ) );

			}
		`,blending:$n,depthTest:!1,depthWrite:!1})}function uc(){return`

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
	`}function pg(i){let e=new WeakMap,t=null;function n(o){if(o&&o.isTexture){let c=o.mapping,l=c===ka||c===Ha,u=c===Ri||c===Ii;if(l||u){let d=e.get(o),h=d!==void 0?d.texture.pmremVersion:0;if(o.isRenderTargetTexture&&o.pmremVersion!==h)return t===null&&(t=new Ao(i)),d=l?t.fromEquirectangular(o,d):t.fromCubemap(o,d),d.texture.pmremVersion=o.pmremVersion,e.set(o,d),d.texture;if(d!==void 0)return d.texture;{let p=o.image;return l&&p&&p.height>0||u&&p&&r(p)?(t===null&&(t=new Ao(i)),d=l?t.fromEquirectangular(o):t.fromCubemap(o),d.texture.pmremVersion=o.pmremVersion,e.set(o,d),o.addEventListener("dispose",s),d.texture):null}}}return o}function r(o){let c=0,l=6;for(let u=0;u<l;u++)o[u]!==void 0&&c++;return c===l}function s(o){let c=o.target;c.removeEventListener("dispose",s);let l=e.get(c);l!==void 0&&(e.delete(c),l.dispose())}function a(){e=new WeakMap,t!==null&&(t.dispose(),t=null)}return{get:n,dispose:a}}function mg(i){let e={};function t(n){if(e[n]!==void 0)return e[n];let r;switch(n){case"WEBGL_depth_texture":r=i.getExtension("WEBGL_depth_texture")||i.getExtension("MOZ_WEBGL_depth_texture")||i.getExtension("WEBKIT_WEBGL_depth_texture");break;case"EXT_texture_filter_anisotropic":r=i.getExtension("EXT_texture_filter_anisotropic")||i.getExtension("MOZ_EXT_texture_filter_anisotropic")||i.getExtension("WEBKIT_EXT_texture_filter_anisotropic");break;case"WEBGL_compressed_texture_s3tc":r=i.getExtension("WEBGL_compressed_texture_s3tc")||i.getExtension("MOZ_WEBGL_compressed_texture_s3tc")||i.getExtension("WEBKIT_WEBGL_compressed_texture_s3tc");break;case"WEBGL_compressed_texture_pvrtc":r=i.getExtension("WEBGL_compressed_texture_pvrtc")||i.getExtension("WEBKIT_WEBGL_compressed_texture_pvrtc");break;default:r=i.getExtension(n)}return e[n]=r,r}return{has:function(n){return t(n)!==null},init:function(){t("EXT_color_buffer_float"),t("WEBGL_clip_cull_distance"),t("OES_texture_float_linear"),t("EXT_color_buffer_half_float"),t("WEBGL_multisampled_render_to_texture"),t("WEBGL_render_shared_exponent")},get:function(n){let r=t(n);return r===null&&ur("THREE.WebGLRenderer: "+n+" extension not supported."),r}}}function gg(i,e,t,n){let r={},s=new WeakMap;function a(d){let h=d.target;h.index!==null&&e.remove(h.index);for(let g in h.attributes)e.remove(h.attributes[g]);h.removeEventListener("dispose",a),delete r[h.id];let p=s.get(h);p&&(e.remove(p),s.delete(h)),n.releaseStatesOfGeometry(h),h.isInstancedBufferGeometry===!0&&delete h._maxInstanceCount,t.memory.geometries--}function o(d,h){return r[h.id]===!0||(h.addEventListener("dispose",a),r[h.id]=!0,t.memory.geometries++),h}function c(d){let h=d.attributes;for(let p in h)e.update(h[p],i.ARRAY_BUFFER)}function l(d){let h=[],p=d.index,g=d.attributes.position,x=0;if(p!==null){let S=p.array;x=p.version;for(let M=0,y=S.length;M<y;M+=3){let C=S[M+0],A=S[M+1],I=S[M+2];h.push(C,A,A,I,I,C)}}else if(g!==void 0){let S=g.array;x=g.version;for(let M=0,y=S.length/3-1;M<y;M+=3){let C=M+0,A=M+1,I=M+2;h.push(C,A,A,I,I,C)}}else return;let m=new($l(h)?qr:$r)(h,1);m.version=x;let f=s.get(d);f&&e.remove(f),s.set(d,m)}function u(d){let h=s.get(d);if(h){let p=d.index;p!==null&&h.version<p.version&&l(d)}else l(d);return s.get(d)}return{get:o,update:c,getWireframeAttribute:u}}function xg(i,e,t){let n;function r(h){n=h}let s,a;function o(h){s=h.type,a=h.bytesPerElement}function c(h,p){i.drawElements(n,p,s,h*a),t.update(p,n,1)}function l(h,p,g){g!==0&&(i.drawElementsInstanced(n,p,s,h*a,g),t.update(p,n,g))}function u(h,p,g){if(g===0)return;e.get("WEBGL_multi_draw").multiDrawElementsWEBGL(n,p,0,s,h,0,g);let m=0;for(let f=0;f<g;f++)m+=p[f];t.update(m,n,1)}function d(h,p,g,x){if(g===0)return;let m=e.get("WEBGL_multi_draw");if(m===null)for(let f=0;f<h.length;f++)l(h[f]/a,p[f],x[f]);else{m.multiDrawElementsInstancedWEBGL(n,p,0,s,h,0,x,0,g);let f=0;for(let S=0;S<g;S++)f+=p[S]*x[S];t.update(f,n,1)}}this.setMode=r,this.setIndex=o,this.render=c,this.renderInstances=l,this.renderMultiDraw=u,this.renderMultiDrawInstances=d}function _g(i){let e={geometries:0,textures:0},t={frame:0,calls:0,triangles:0,points:0,lines:0};function n(s,a,o){switch(t.calls++,a){case i.TRIANGLES:t.triangles+=o*(s/3);break;case i.LINES:t.lines+=o*(s/2);break;case i.LINE_STRIP:t.lines+=o*(s-1);break;case i.LINE_LOOP:t.lines+=o*s;break;case i.POINTS:t.points+=o*s;break;default:console.error("THREE.WebGLInfo: Unknown draw mode:",a);break}}function r(){t.calls=0,t.triangles=0,t.points=0,t.lines=0}return{memory:e,render:t,programs:null,autoReset:!0,reset:r,update:n}}function yg(i,e,t){let n=new WeakMap,r=new xt;function s(a,o,c){let l=a.morphTargetInfluences,u=o.morphAttributes.position||o.morphAttributes.normal||o.morphAttributes.color,d=u!==void 0?u.length:0,h=n.get(o);if(h===void 0||h.count!==d){let v=function(){I.dispose(),n.delete(o),o.removeEventListener("dispose",v)};h!==void 0&&h.texture.dispose();let p=o.morphAttributes.position!==void 0,g=o.morphAttributes.normal!==void 0,x=o.morphAttributes.color!==void 0,m=o.morphAttributes.position||[],f=o.morphAttributes.normal||[],S=o.morphAttributes.color||[],M=0;p===!0&&(M=1),g===!0&&(M=2),x===!0&&(M=3);let y=o.attributes.position.count*M,C=1;y>e.maxTextureSize&&(C=Math.ceil(y/e.maxTextureSize),y=e.maxTextureSize);let A=new Float32Array(y*C*4*d),I=new Wr(A,y,C,d);I.type=Nn,I.needsUpdate=!0;let N=M*4;for(let b=0;b<d;b++){let T=m[b],P=f[b],U=S[b],F=y*C*4*b;for(let k=0;k<T.count;k++){let G=k*N;p===!0&&(r.fromBufferAttribute(T,k),A[F+G+0]=r.x,A[F+G+1]=r.y,A[F+G+2]=r.z,A[F+G+3]=0),g===!0&&(r.fromBufferAttribute(P,k),A[F+G+4]=r.x,A[F+G+5]=r.y,A[F+G+6]=r.z,A[F+G+7]=0),x===!0&&(r.fromBufferAttribute(U,k),A[F+G+8]=r.x,A[F+G+9]=r.y,A[F+G+10]=r.z,A[F+G+11]=U.itemSize===4?r.w:1)}}h={count:d,texture:I,size:new We(y,C)},n.set(o,h),o.addEventListener("dispose",v)}if(a.isInstancedMesh===!0&&a.morphTexture!==null)c.getUniforms().setValue(i,"morphTexture",a.morphTexture,t);else{let p=0;for(let x=0;x<l.length;x++)p+=l[x];let g=o.morphTargetsRelative?1:1-p;c.getUniforms().setValue(i,"morphTargetBaseInfluence",g),c.getUniforms().setValue(i,"morphTargetInfluences",l)}c.getUniforms().setValue(i,"morphTargetsTexture",h.texture,t),c.getUniforms().setValue(i,"morphTargetsTextureSize",h.size)}return{update:s}}function vg(i,e,t,n){let r=new WeakMap;function s(c){let l=n.render.frame,u=c.geometry,d=e.get(c,u);if(r.get(d)!==l&&(e.update(d),r.set(d,l)),c.isInstancedMesh&&(c.hasEventListener("dispose",o)===!1&&c.addEventListener("dispose",o),r.get(c)!==l&&(t.update(c.instanceMatrix,i.ARRAY_BUFFER),c.instanceColor!==null&&t.update(c.instanceColor,i.ARRAY_BUFFER),r.set(c,l))),c.isSkinnedMesh){let h=c.skeleton;r.get(h)!==l&&(h.update(),r.set(h,l))}return d}function a(){r=new WeakMap}function o(c){let l=c.target;l.removeEventListener("dispose",o),t.remove(l.instanceMatrix),l.instanceColor!==null&&t.remove(l.instanceColor)}return{update:s,dispose:a}}var Nu=new Lt,pu=new ts(1,1),Du=new Wr,Lu=new pa,Fu=new Zr,mu=[],gu=[],xu=new Float32Array(16),_u=new Float32Array(9),yu=new Float32Array(4);function Er(i,e,t){let n=i[0];if(n<=0||n>0)return i;let r=e*t,s=mu[r];if(s===void 0&&(s=new Float32Array(r),mu[r]=s),e!==0){n.toArray(s,0);for(let a=1,o=0;a!==e;++a)o+=t,i[a].toArray(s,o)}return s}function Et(i,e){if(i.length!==e.length)return!1;for(let t=0,n=i.length;t<n;t++)if(i[t]!==e[t])return!1;return!0}function Tt(i,e){for(let t=0,n=e.length;t<n;t++)i[t]=e[t]}function Ro(i,e){let t=gu[e];t===void 0&&(t=new Int32Array(e),gu[e]=t);for(let n=0;n!==e;++n)t[n]=i.allocateTextureUnit();return t}function bg(i,e){let t=this.cache;t[0]!==e&&(i.uniform1f(this.addr,e),t[0]=e)}function wg(i,e){let t=this.cache;if(e.x!==void 0)(t[0]!==e.x||t[1]!==e.y)&&(i.uniform2f(this.addr,e.x,e.y),t[0]=e.x,t[1]=e.y);else{if(Et(t,e))return;i.uniform2fv(this.addr,e),Tt(t,e)}}function Mg(i,e){let t=this.cache;if(e.x!==void 0)(t[0]!==e.x||t[1]!==e.y||t[2]!==e.z)&&(i.uniform3f(this.addr,e.x,e.y,e.z),t[0]=e.x,t[1]=e.y,t[2]=e.z);else if(e.r!==void 0)(t[0]!==e.r||t[1]!==e.g||t[2]!==e.b)&&(i.uniform3f(this.addr,e.r,e.g,e.b),t[0]=e.r,t[1]=e.g,t[2]=e.b);else{if(Et(t,e))return;i.uniform3fv(this.addr,e),Tt(t,e)}}function Sg(i,e){let t=this.cache;if(e.x!==void 0)(t[0]!==e.x||t[1]!==e.y||t[2]!==e.z||t[3]!==e.w)&&(i.uniform4f(this.addr,e.x,e.y,e.z,e.w),t[0]=e.x,t[1]=e.y,t[2]=e.z,t[3]=e.w);else{if(Et(t,e))return;i.uniform4fv(this.addr,e),Tt(t,e)}}function Eg(i,e){let t=this.cache,n=e.elements;if(n===void 0){if(Et(t,e))return;i.uniformMatrix2fv(this.addr,!1,e),Tt(t,e)}else{if(Et(t,n))return;yu.set(n),i.uniformMatrix2fv(this.addr,!1,yu),Tt(t,n)}}function Tg(i,e){let t=this.cache,n=e.elements;if(n===void 0){if(Et(t,e))return;i.uniformMatrix3fv(this.addr,!1,e),Tt(t,e)}else{if(Et(t,n))return;_u.set(n),i.uniformMatrix3fv(this.addr,!1,_u),Tt(t,n)}}function Ag(i,e){let t=this.cache,n=e.elements;if(n===void 0){if(Et(t,e))return;i.uniformMatrix4fv(this.addr,!1,e),Tt(t,e)}else{if(Et(t,n))return;xu.set(n),i.uniformMatrix4fv(this.addr,!1,xu),Tt(t,n)}}function Cg(i,e){let t=this.cache;t[0]!==e&&(i.uniform1i(this.addr,e),t[0]=e)}function Rg(i,e){let t=this.cache;if(e.x!==void 0)(t[0]!==e.x||t[1]!==e.y)&&(i.uniform2i(this.addr,e.x,e.y),t[0]=e.x,t[1]=e.y);else{if(Et(t,e))return;i.uniform2iv(this.addr,e),Tt(t,e)}}function Ig(i,e){let t=this.cache;if(e.x!==void 0)(t[0]!==e.x||t[1]!==e.y||t[2]!==e.z)&&(i.uniform3i(this.addr,e.x,e.y,e.z),t[0]=e.x,t[1]=e.y,t[2]=e.z);else{if(Et(t,e))return;i.uniform3iv(this.addr,e),Tt(t,e)}}function Pg(i,e){let t=this.cache;if(e.x!==void 0)(t[0]!==e.x||t[1]!==e.y||t[2]!==e.z||t[3]!==e.w)&&(i.uniform4i(this.addr,e.x,e.y,e.z,e.w),t[0]=e.x,t[1]=e.y,t[2]=e.z,t[3]=e.w);else{if(Et(t,e))return;i.uniform4iv(this.addr,e),Tt(t,e)}}function Ng(i,e){let t=this.cache;t[0]!==e&&(i.uniform1ui(this.addr,e),t[0]=e)}function Dg(i,e){let t=this.cache;if(e.x!==void 0)(t[0]!==e.x||t[1]!==e.y)&&(i.uniform2ui(this.addr,e.x,e.y),t[0]=e.x,t[1]=e.y);else{if(Et(t,e))return;i.uniform2uiv(this.addr,e),Tt(t,e)}}function Lg(i,e){let t=this.cache;if(e.x!==void 0)(t[0]!==e.x||t[1]!==e.y||t[2]!==e.z)&&(i.uniform3ui(this.addr,e.x,e.y,e.z),t[0]=e.x,t[1]=e.y,t[2]=e.z);else{if(Et(t,e))return;i.uniform3uiv(this.addr,e),Tt(t,e)}}function Fg(i,e){let t=this.cache;if(e.x!==void 0)(t[0]!==e.x||t[1]!==e.y||t[2]!==e.z||t[3]!==e.w)&&(i.uniform4ui(this.addr,e.x,e.y,e.z,e.w),t[0]=e.x,t[1]=e.y,t[2]=e.z,t[3]=e.w);else{if(Et(t,e))return;i.uniform4uiv(this.addr,e),Tt(t,e)}}function Ug(i,e,t){let n=this.cache,r=t.allocateTextureUnit();n[0]!==r&&(i.uniform1i(this.addr,r),n[0]=r);let s;this.type===i.SAMPLER_2D_SHADOW?(pu.compareFunction=Gl,s=pu):s=Nu,t.setTexture2D(e||s,r)}function Og(i,e,t){let n=this.cache,r=t.allocateTextureUnit();n[0]!==r&&(i.uniform1i(this.addr,r),n[0]=r),t.setTexture3D(e||Lu,r)}function Bg(i,e,t){let n=this.cache,r=t.allocateTextureUnit();n[0]!==r&&(i.uniform1i(this.addr,r),n[0]=r),t.setTextureCube(e||Fu,r)}function zg(i,e,t){let n=this.cache,r=t.allocateTextureUnit();n[0]!==r&&(i.uniform1i(this.addr,r),n[0]=r),t.setTexture2DArray(e||Du,r)}function kg(i){switch(i){case 5126:return bg;case 35664:return wg;case 35665:return Mg;case 35666:return Sg;case 35674:return Eg;case 35675:return Tg;case 35676:return Ag;case 5124:case 35670:return Cg;case 35667:case 35671:return Rg;case 35668:case 35672:return Ig;case 35669:case 35673:return Pg;case 5125:return Ng;case 36294:return Dg;case 36295:return Lg;case 36296:return Fg;case 35678:case 36198:case 36298:case 36306:case 35682:return Ug;case 35679:case 36299:case 36307:return Og;case 35680:case 36300:case 36308:case 36293:return Bg;case 36289:case 36303:case 36311:case 36292:return zg}}function Hg(i,e){i.uniform1fv(this.addr,e)}function Vg(i,e){let t=Er(e,this.size,2);i.uniform2fv(this.addr,t)}function Gg(i,e){let t=Er(e,this.size,3);i.uniform3fv(this.addr,t)}function Wg(i,e){let t=Er(e,this.size,4);i.uniform4fv(this.addr,t)}function Xg(i,e){let t=Er(e,this.size,4);i.uniformMatrix2fv(this.addr,!1,t)}function $g(i,e){let t=Er(e,this.size,9);i.uniformMatrix3fv(this.addr,!1,t)}function qg(i,e){let t=Er(e,this.size,16);i.uniformMatrix4fv(this.addr,!1,t)}function Yg(i,e){i.uniform1iv(this.addr,e)}function Zg(i,e){i.uniform2iv(this.addr,e)}function Jg(i,e){i.uniform3iv(this.addr,e)}function Kg(i,e){i.uniform4iv(this.addr,e)}function jg(i,e){i.uniform1uiv(this.addr,e)}function Qg(i,e){i.uniform2uiv(this.addr,e)}function e0(i,e){i.uniform3uiv(this.addr,e)}function t0(i,e){i.uniform4uiv(this.addr,e)}function n0(i,e,t){let n=this.cache,r=e.length,s=Ro(t,r);Et(n,s)||(i.uniform1iv(this.addr,s),Tt(n,s));for(let a=0;a!==r;++a)t.setTexture2D(e[a]||Nu,s[a])}function i0(i,e,t){let n=this.cache,r=e.length,s=Ro(t,r);Et(n,s)||(i.uniform1iv(this.addr,s),Tt(n,s));for(let a=0;a!==r;++a)t.setTexture3D(e[a]||Lu,s[a])}function r0(i,e,t){let n=this.cache,r=e.length,s=Ro(t,r);Et(n,s)||(i.uniform1iv(this.addr,s),Tt(n,s));for(let a=0;a!==r;++a)t.setTextureCube(e[a]||Fu,s[a])}function s0(i,e,t){let n=this.cache,r=e.length,s=Ro(t,r);Et(n,s)||(i.uniform1iv(this.addr,s),Tt(n,s));for(let a=0;a!==r;++a)t.setTexture2DArray(e[a]||Du,s[a])}function a0(i){switch(i){case 5126:return Hg;case 35664:return Vg;case 35665:return Gg;case 35666:return Wg;case 35674:return Xg;case 35675:return $g;case 35676:return qg;case 5124:case 35670:return Yg;case 35667:case 35671:return Zg;case 35668:case 35672:return Jg;case 35669:case 35673:return Kg;case 5125:return jg;case 36294:return Qg;case 36295:return e0;case 36296:return t0;case 35678:case 36198:case 36298:case 36306:case 35682:return n0;case 35679:case 36299:case 36307:return i0;case 35680:case 36300:case 36308:case 36293:return r0;case 36289:case 36303:case 36311:case 36292:return s0}}var ic=class{constructor(e,t,n){this.id=e,this.addr=n,this.cache=[],this.type=t.type,this.setValue=kg(t.type)}},rc=class{constructor(e,t,n){this.id=e,this.addr=n,this.cache=[],this.type=t.type,this.size=t.size,this.setValue=a0(t.type)}},sc=class{constructor(e){this.id=e,this.seq=[],this.map={}}setValue(e,t,n){let r=this.seq;for(let s=0,a=r.length;s!==a;++s){let o=r[s];o.setValue(e,t[o.id],n)}}},nc=/(\w+)(\])?(\[|\.)?/g;function vu(i,e){i.seq.push(e),i.map[e.id]=e}function o0(i,e,t){let n=i.name,r=n.length;for(nc.lastIndex=0;;){let s=nc.exec(n),a=nc.lastIndex,o=s[1],c=s[2]==="]",l=s[3];if(c&&(o=o|0),l===void 0||l==="["&&a+2===r){vu(t,l===void 0?new ic(o,i,e):new rc(o,i,e));break}else{let d=t.map[o];d===void 0&&(d=new sc(o),vu(t,d)),t=d}}}var Sr=class{constructor(e,t){this.seq=[],this.map={};let n=e.getProgramParameter(t,e.ACTIVE_UNIFORMS);for(let r=0;r<n;++r){let s=e.getActiveUniform(t,r),a=e.getUniformLocation(t,s.name);o0(s,a,this)}}setValue(e,t,n,r){let s=this.map[t];s!==void 0&&s.setValue(e,n,r)}setOptional(e,t,n){let r=t[n];r!==void 0&&this.setValue(e,n,r)}static upload(e,t,n,r){for(let s=0,a=t.length;s!==a;++s){let o=t[s],c=n[o.id];c.needsUpdate!==!1&&o.setValue(e,c.value,r)}}static seqWithValue(e,t){let n=[];for(let r=0,s=e.length;r!==s;++r){let a=e[r];a.id in t&&n.push(a)}return n}};function bu(i,e,t){let n=i.createShader(e);return i.shaderSource(n,t),i.compileShader(n),n}var l0=37297,c0=0;function d0(i,e){let t=i.split(`
`),n=[],r=Math.max(e-6,0),s=Math.min(e+6,t.length);for(let a=r;a<s;a++){let o=a+1;n.push(`${o===e?">":" "} ${o}: ${t[a]}`)}return n.join(`
`)}var wu=new ke;function u0(i){Ke._getMatrix(wu,Ke.workingColorSpace,i);let e=`mat3( ${wu.elements.map(t=>t.toFixed(4))} )`;switch(Ke.getTransfer(i)){case Hr:return[e,"LinearTransferOETF"];case tt:return[e,"sRGBTransferOETF"];default:return console.warn("THREE.WebGLProgram: Unsupported color space: ",i),[e,"LinearTransferOETF"]}}function Mu(i,e,t){let n=i.getShaderParameter(e,i.COMPILE_STATUS),s=(i.getShaderInfoLog(e)||"").trim();if(n&&s==="")return"";let a=/ERROR: 0:(\d+)/.exec(s);if(a){let o=parseInt(a[1]);return t.toUpperCase()+`

`+s+`

`+d0(i.getShaderSource(e),o)}else return s}function h0(i,e){let t=u0(e);return[`vec4 ${i}( vec4 value ) {`,`	return ${t[1]}( vec4( value.rgb * ${t[0]}, value.a ) );`,"}"].join(`
`)}function f0(i,e){let t;switch(e){case Bd:t="Linear";break;case zd:t="Reinhard";break;case kd:t="Cineon";break;case Hd:t="ACESFilmic";break;case Gd:t="AgX";break;case Wd:t="Neutral";break;case Vd:t="Custom";break;default:console.warn("THREE.WebGLProgram: Unsupported toneMapping:",e),t="Linear"}return"vec3 "+i+"( vec3 color ) { return "+t+"ToneMapping( color ); }"}var To=new D;function p0(){Ke.getLuminanceCoefficients(To);let i=To.x.toFixed(4),e=To.y.toFixed(4),t=To.z.toFixed(4);return["float luminance( const in vec3 rgb ) {",`	const vec3 weights = vec3( ${i}, ${e}, ${t} );`,"	return dot( weights, rgb );","}"].join(`
`)}function m0(i){return[i.extensionClipCullDistance?"#extension GL_ANGLE_clip_cull_distance : require":"",i.extensionMultiDraw?"#extension GL_ANGLE_multi_draw : require":""].filter(ys).join(`
`)}function g0(i){let e=[];for(let t in i){let n=i[t];n!==!1&&e.push("#define "+t+" "+n)}return e.join(`
`)}function x0(i,e){let t={},n=i.getProgramParameter(e,i.ACTIVE_ATTRIBUTES);for(let r=0;r<n;r++){let s=i.getActiveAttrib(e,r),a=s.name,o=1;s.type===i.FLOAT_MAT2&&(o=2),s.type===i.FLOAT_MAT3&&(o=3),s.type===i.FLOAT_MAT4&&(o=4),t[a]={type:s.type,location:i.getAttribLocation(e,a),locationSize:o}}return t}function ys(i){return i!==""}function Su(i,e){let t=e.numSpotLightShadows+e.numSpotLightMaps-e.numSpotLightShadowsWithMaps;return i.replace(/NUM_DIR_LIGHTS/g,e.numDirLights).replace(/NUM_SPOT_LIGHTS/g,e.numSpotLights).replace(/NUM_SPOT_LIGHT_MAPS/g,e.numSpotLightMaps).replace(/NUM_SPOT_LIGHT_COORDS/g,t).replace(/NUM_RECT_AREA_LIGHTS/g,e.numRectAreaLights).replace(/NUM_POINT_LIGHTS/g,e.numPointLights).replace(/NUM_HEMI_LIGHTS/g,e.numHemiLights).replace(/NUM_DIR_LIGHT_SHADOWS/g,e.numDirLightShadows).replace(/NUM_SPOT_LIGHT_SHADOWS_WITH_MAPS/g,e.numSpotLightShadowsWithMaps).replace(/NUM_SPOT_LIGHT_SHADOWS/g,e.numSpotLightShadows).replace(/NUM_POINT_LIGHT_SHADOWS/g,e.numPointLightShadows)}function Eu(i,e){return i.replace(/NUM_CLIPPING_PLANES/g,e.numClippingPlanes).replace(/UNION_CLIPPING_PLANES/g,e.numClippingPlanes-e.numClipIntersection)}var _0=/^[ \t]*#include +<([\w\d./]+)>/gm;function ac(i){return i.replace(_0,v0)}var y0=new Map;function v0(i,e){let t=Xe[e];if(t===void 0){let n=y0.get(e);if(n!==void 0)t=Xe[n],console.warn('THREE.WebGLRenderer: Shader chunk "%s" has been deprecated. Use "%s" instead.',e,n);else throw new Error("Can not resolve #include <"+e+">")}return ac(t)}var b0=/#pragma unroll_loop_start\s+for\s*\(\s*int\s+i\s*=\s*(\d+)\s*;\s*i\s*<\s*(\d+)\s*;\s*i\s*\+\+\s*\)\s*{([\s\S]+?)}\s+#pragma unroll_loop_end/g;function Tu(i){return i.replace(b0,w0)}function w0(i,e,t,n){let r="";for(let s=parseInt(e);s<parseInt(t);s++)r+=n.replace(/\[\s*i\s*\]/g,"[ "+s+" ]").replace(/UNROLLED_LOOP_INDEX/g,s);return r}function Au(i){let e=`precision ${i.precision} float;
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
#define LOW_PRECISION`),e}function M0(i){let e="SHADOWMAP_TYPE_BASIC";return i.shadowMapType===Cl?e="SHADOWMAP_TYPE_PCF":i.shadowMapType===xd?e="SHADOWMAP_TYPE_PCF_SOFT":i.shadowMapType===Pn&&(e="SHADOWMAP_TYPE_VSM"),e}function S0(i){let e="ENVMAP_TYPE_CUBE";if(i.envMap)switch(i.envMapMode){case Ri:case Ii:e="ENVMAP_TYPE_CUBE";break;case fs:e="ENVMAP_TYPE_CUBE_UV";break}return e}function E0(i){let e="ENVMAP_MODE_REFLECTION";if(i.envMap)switch(i.envMapMode){case Ii:e="ENVMAP_MODE_REFRACTION";break}return e}function T0(i){let e="ENVMAP_BLENDING_NONE";if(i.envMap)switch(i.combine){case Nl:e="ENVMAP_BLENDING_MULTIPLY";break;case Ud:e="ENVMAP_BLENDING_MIX";break;case Od:e="ENVMAP_BLENDING_ADD";break}return e}function A0(i){let e=i.envMapCubeUVHeight;if(e===null)return null;let t=Math.log2(e)-2,n=1/e;return{texelWidth:1/(3*Math.max(Math.pow(2,t),112)),texelHeight:n,maxMip:t}}function C0(i,e,t,n){let r=i.getContext(),s=t.defines,a=t.vertexShader,o=t.fragmentShader,c=M0(t),l=S0(t),u=E0(t),d=T0(t),h=A0(t),p=m0(t),g=g0(s),x=r.createProgram(),m,f,S=t.glslVersion?"#version "+t.glslVersion+`
`:"";t.isRawShaderMaterial?(m=["#define SHADER_TYPE "+t.shaderType,"#define SHADER_NAME "+t.shaderName,g].filter(ys).join(`
`),m.length>0&&(m+=`
`),f=["#define SHADER_TYPE "+t.shaderType,"#define SHADER_NAME "+t.shaderName,g].filter(ys).join(`
`),f.length>0&&(f+=`
`)):(m=[Au(t),"#define SHADER_TYPE "+t.shaderType,"#define SHADER_NAME "+t.shaderName,g,t.extensionClipCullDistance?"#define USE_CLIP_DISTANCE":"",t.batching?"#define USE_BATCHING":"",t.batchingColor?"#define USE_BATCHING_COLOR":"",t.instancing?"#define USE_INSTANCING":"",t.instancingColor?"#define USE_INSTANCING_COLOR":"",t.instancingMorph?"#define USE_INSTANCING_MORPH":"",t.useFog&&t.fog?"#define USE_FOG":"",t.useFog&&t.fogExp2?"#define FOG_EXP2":"",t.map?"#define USE_MAP":"",t.envMap?"#define USE_ENVMAP":"",t.envMap?"#define "+u:"",t.lightMap?"#define USE_LIGHTMAP":"",t.aoMap?"#define USE_AOMAP":"",t.bumpMap?"#define USE_BUMPMAP":"",t.normalMap?"#define USE_NORMALMAP":"",t.normalMapObjectSpace?"#define USE_NORMALMAP_OBJECTSPACE":"",t.normalMapTangentSpace?"#define USE_NORMALMAP_TANGENTSPACE":"",t.displacementMap?"#define USE_DISPLACEMENTMAP":"",t.emissiveMap?"#define USE_EMISSIVEMAP":"",t.anisotropy?"#define USE_ANISOTROPY":"",t.anisotropyMap?"#define USE_ANISOTROPYMAP":"",t.clearcoatMap?"#define USE_CLEARCOATMAP":"",t.clearcoatRoughnessMap?"#define USE_CLEARCOAT_ROUGHNESSMAP":"",t.clearcoatNormalMap?"#define USE_CLEARCOAT_NORMALMAP":"",t.iridescenceMap?"#define USE_IRIDESCENCEMAP":"",t.iridescenceThicknessMap?"#define USE_IRIDESCENCE_THICKNESSMAP":"",t.specularMap?"#define USE_SPECULARMAP":"",t.specularColorMap?"#define USE_SPECULAR_COLORMAP":"",t.specularIntensityMap?"#define USE_SPECULAR_INTENSITYMAP":"",t.roughnessMap?"#define USE_ROUGHNESSMAP":"",t.metalnessMap?"#define USE_METALNESSMAP":"",t.alphaMap?"#define USE_ALPHAMAP":"",t.alphaHash?"#define USE_ALPHAHASH":"",t.transmission?"#define USE_TRANSMISSION":"",t.transmissionMap?"#define USE_TRANSMISSIONMAP":"",t.thicknessMap?"#define USE_THICKNESSMAP":"",t.sheenColorMap?"#define USE_SHEEN_COLORMAP":"",t.sheenRoughnessMap?"#define USE_SHEEN_ROUGHNESSMAP":"",t.mapUv?"#define MAP_UV "+t.mapUv:"",t.alphaMapUv?"#define ALPHAMAP_UV "+t.alphaMapUv:"",t.lightMapUv?"#define LIGHTMAP_UV "+t.lightMapUv:"",t.aoMapUv?"#define AOMAP_UV "+t.aoMapUv:"",t.emissiveMapUv?"#define EMISSIVEMAP_UV "+t.emissiveMapUv:"",t.bumpMapUv?"#define BUMPMAP_UV "+t.bumpMapUv:"",t.normalMapUv?"#define NORMALMAP_UV "+t.normalMapUv:"",t.displacementMapUv?"#define DISPLACEMENTMAP_UV "+t.displacementMapUv:"",t.metalnessMapUv?"#define METALNESSMAP_UV "+t.metalnessMapUv:"",t.roughnessMapUv?"#define ROUGHNESSMAP_UV "+t.roughnessMapUv:"",t.anisotropyMapUv?"#define ANISOTROPYMAP_UV "+t.anisotropyMapUv:"",t.clearcoatMapUv?"#define CLEARCOATMAP_UV "+t.clearcoatMapUv:"",t.clearcoatNormalMapUv?"#define CLEARCOAT_NORMALMAP_UV "+t.clearcoatNormalMapUv:"",t.clearcoatRoughnessMapUv?"#define CLEARCOAT_ROUGHNESSMAP_UV "+t.clearcoatRoughnessMapUv:"",t.iridescenceMapUv?"#define IRIDESCENCEMAP_UV "+t.iridescenceMapUv:"",t.iridescenceThicknessMapUv?"#define IRIDESCENCE_THICKNESSMAP_UV "+t.iridescenceThicknessMapUv:"",t.sheenColorMapUv?"#define SHEEN_COLORMAP_UV "+t.sheenColorMapUv:"",t.sheenRoughnessMapUv?"#define SHEEN_ROUGHNESSMAP_UV "+t.sheenRoughnessMapUv:"",t.specularMapUv?"#define SPECULARMAP_UV "+t.specularMapUv:"",t.specularColorMapUv?"#define SPECULAR_COLORMAP_UV "+t.specularColorMapUv:"",t.specularIntensityMapUv?"#define SPECULAR_INTENSITYMAP_UV "+t.specularIntensityMapUv:"",t.transmissionMapUv?"#define TRANSMISSIONMAP_UV "+t.transmissionMapUv:"",t.thicknessMapUv?"#define THICKNESSMAP_UV "+t.thicknessMapUv:"",t.vertexTangents&&t.flatShading===!1?"#define USE_TANGENT":"",t.vertexColors?"#define USE_COLOR":"",t.vertexAlphas?"#define USE_COLOR_ALPHA":"",t.vertexUv1s?"#define USE_UV1":"",t.vertexUv2s?"#define USE_UV2":"",t.vertexUv3s?"#define USE_UV3":"",t.pointsUvs?"#define USE_POINTS_UV":"",t.flatShading?"#define FLAT_SHADED":"",t.skinning?"#define USE_SKINNING":"",t.morphTargets?"#define USE_MORPHTARGETS":"",t.morphNormals&&t.flatShading===!1?"#define USE_MORPHNORMALS":"",t.morphColors?"#define USE_MORPHCOLORS":"",t.morphTargetsCount>0?"#define MORPHTARGETS_TEXTURE_STRIDE "+t.morphTextureStride:"",t.morphTargetsCount>0?"#define MORPHTARGETS_COUNT "+t.morphTargetsCount:"",t.doubleSided?"#define DOUBLE_SIDED":"",t.flipSided?"#define FLIP_SIDED":"",t.shadowMapEnabled?"#define USE_SHADOWMAP":"",t.shadowMapEnabled?"#define "+c:"",t.sizeAttenuation?"#define USE_SIZEATTENUATION":"",t.numLightProbes>0?"#define USE_LIGHT_PROBES":"",t.logarithmicDepthBuffer?"#define USE_LOGARITHMIC_DEPTH_BUFFER":"",t.reversedDepthBuffer?"#define USE_REVERSED_DEPTH_BUFFER":"","uniform mat4 modelMatrix;","uniform mat4 modelViewMatrix;","uniform mat4 projectionMatrix;","uniform mat4 viewMatrix;","uniform mat3 normalMatrix;","uniform vec3 cameraPosition;","uniform bool isOrthographic;","#ifdef USE_INSTANCING","	attribute mat4 instanceMatrix;","#endif","#ifdef USE_INSTANCING_COLOR","	attribute vec3 instanceColor;","#endif","#ifdef USE_INSTANCING_MORPH","	uniform sampler2D morphTexture;","#endif","attribute vec3 position;","attribute vec3 normal;","attribute vec2 uv;","#ifdef USE_UV1","	attribute vec2 uv1;","#endif","#ifdef USE_UV2","	attribute vec2 uv2;","#endif","#ifdef USE_UV3","	attribute vec2 uv3;","#endif","#ifdef USE_TANGENT","	attribute vec4 tangent;","#endif","#if defined( USE_COLOR_ALPHA )","	attribute vec4 color;","#elif defined( USE_COLOR )","	attribute vec3 color;","#endif","#ifdef USE_SKINNING","	attribute vec4 skinIndex;","	attribute vec4 skinWeight;","#endif",`
`].filter(ys).join(`
`),f=[Au(t),"#define SHADER_TYPE "+t.shaderType,"#define SHADER_NAME "+t.shaderName,g,t.useFog&&t.fog?"#define USE_FOG":"",t.useFog&&t.fogExp2?"#define FOG_EXP2":"",t.alphaToCoverage?"#define ALPHA_TO_COVERAGE":"",t.map?"#define USE_MAP":"",t.matcap?"#define USE_MATCAP":"",t.envMap?"#define USE_ENVMAP":"",t.envMap?"#define "+l:"",t.envMap?"#define "+u:"",t.envMap?"#define "+d:"",h?"#define CUBEUV_TEXEL_WIDTH "+h.texelWidth:"",h?"#define CUBEUV_TEXEL_HEIGHT "+h.texelHeight:"",h?"#define CUBEUV_MAX_MIP "+h.maxMip+".0":"",t.lightMap?"#define USE_LIGHTMAP":"",t.aoMap?"#define USE_AOMAP":"",t.bumpMap?"#define USE_BUMPMAP":"",t.normalMap?"#define USE_NORMALMAP":"",t.normalMapObjectSpace?"#define USE_NORMALMAP_OBJECTSPACE":"",t.normalMapTangentSpace?"#define USE_NORMALMAP_TANGENTSPACE":"",t.emissiveMap?"#define USE_EMISSIVEMAP":"",t.anisotropy?"#define USE_ANISOTROPY":"",t.anisotropyMap?"#define USE_ANISOTROPYMAP":"",t.clearcoat?"#define USE_CLEARCOAT":"",t.clearcoatMap?"#define USE_CLEARCOATMAP":"",t.clearcoatRoughnessMap?"#define USE_CLEARCOAT_ROUGHNESSMAP":"",t.clearcoatNormalMap?"#define USE_CLEARCOAT_NORMALMAP":"",t.dispersion?"#define USE_DISPERSION":"",t.iridescence?"#define USE_IRIDESCENCE":"",t.iridescenceMap?"#define USE_IRIDESCENCEMAP":"",t.iridescenceThicknessMap?"#define USE_IRIDESCENCE_THICKNESSMAP":"",t.specularMap?"#define USE_SPECULARMAP":"",t.specularColorMap?"#define USE_SPECULAR_COLORMAP":"",t.specularIntensityMap?"#define USE_SPECULAR_INTENSITYMAP":"",t.roughnessMap?"#define USE_ROUGHNESSMAP":"",t.metalnessMap?"#define USE_METALNESSMAP":"",t.alphaMap?"#define USE_ALPHAMAP":"",t.alphaTest?"#define USE_ALPHATEST":"",t.alphaHash?"#define USE_ALPHAHASH":"",t.sheen?"#define USE_SHEEN":"",t.sheenColorMap?"#define USE_SHEEN_COLORMAP":"",t.sheenRoughnessMap?"#define USE_SHEEN_ROUGHNESSMAP":"",t.transmission?"#define USE_TRANSMISSION":"",t.transmissionMap?"#define USE_TRANSMISSIONMAP":"",t.thicknessMap?"#define USE_THICKNESSMAP":"",t.vertexTangents&&t.flatShading===!1?"#define USE_TANGENT":"",t.vertexColors||t.instancingColor||t.batchingColor?"#define USE_COLOR":"",t.vertexAlphas?"#define USE_COLOR_ALPHA":"",t.vertexUv1s?"#define USE_UV1":"",t.vertexUv2s?"#define USE_UV2":"",t.vertexUv3s?"#define USE_UV3":"",t.pointsUvs?"#define USE_POINTS_UV":"",t.gradientMap?"#define USE_GRADIENTMAP":"",t.flatShading?"#define FLAT_SHADED":"",t.doubleSided?"#define DOUBLE_SIDED":"",t.flipSided?"#define FLIP_SIDED":"",t.shadowMapEnabled?"#define USE_SHADOWMAP":"",t.shadowMapEnabled?"#define "+c:"",t.premultipliedAlpha?"#define PREMULTIPLIED_ALPHA":"",t.numLightProbes>0?"#define USE_LIGHT_PROBES":"",t.decodeVideoTexture?"#define DECODE_VIDEO_TEXTURE":"",t.decodeVideoTextureEmissive?"#define DECODE_VIDEO_TEXTURE_EMISSIVE":"",t.logarithmicDepthBuffer?"#define USE_LOGARITHMIC_DEPTH_BUFFER":"",t.reversedDepthBuffer?"#define USE_REVERSED_DEPTH_BUFFER":"","uniform mat4 viewMatrix;","uniform vec3 cameraPosition;","uniform bool isOrthographic;",t.toneMapping!==qn?"#define TONE_MAPPING":"",t.toneMapping!==qn?Xe.tonemapping_pars_fragment:"",t.toneMapping!==qn?f0("toneMapping",t.toneMapping):"",t.dithering?"#define DITHERING":"",t.opaque?"#define OPAQUE":"",Xe.colorspace_pars_fragment,h0("linearToOutputTexel",t.outputColorSpace),p0(),t.useDepthPacking?"#define DEPTH_PACKING "+t.depthPacking:"",`
`].filter(ys).join(`
`)),a=ac(a),a=Su(a,t),a=Eu(a,t),o=ac(o),o=Su(o,t),o=Eu(o,t),a=Tu(a),o=Tu(o),t.isRawShaderMaterial!==!0&&(S=`#version 300 es
`,m=[p,"#define attribute in","#define varying out","#define texture2D texture"].join(`
`)+`
`+m,f=["#define varying in",t.glslVersion===Wl?"":"layout(location = 0) out highp vec4 pc_fragColor;",t.glslVersion===Wl?"":"#define gl_FragColor pc_fragColor","#define gl_FragDepthEXT gl_FragDepth","#define texture2D texture","#define textureCube texture","#define texture2DProj textureProj","#define texture2DLodEXT textureLod","#define texture2DProjLodEXT textureProjLod","#define textureCubeLodEXT textureLod","#define texture2DGradEXT textureGrad","#define texture2DProjGradEXT textureProjGrad","#define textureCubeGradEXT textureGrad"].join(`
`)+`
`+f);let M=S+m+a,y=S+f+o,C=bu(r,r.VERTEX_SHADER,M),A=bu(r,r.FRAGMENT_SHADER,y);r.attachShader(x,C),r.attachShader(x,A),t.index0AttributeName!==void 0?r.bindAttribLocation(x,0,t.index0AttributeName):t.morphTargets===!0&&r.bindAttribLocation(x,0,"position"),r.linkProgram(x);function I(T){if(i.debug.checkShaderErrors){let P=r.getProgramInfoLog(x)||"",U=r.getShaderInfoLog(C)||"",F=r.getShaderInfoLog(A)||"",k=P.trim(),G=U.trim(),K=F.trim(),W=!0,se=!0;if(r.getProgramParameter(x,r.LINK_STATUS)===!1)if(W=!1,typeof i.debug.onShaderError=="function")i.debug.onShaderError(r,x,C,A);else{let de=Mu(r,C,"vertex"),Ae=Mu(r,A,"fragment");console.error("THREE.WebGLProgram: Shader Error "+r.getError()+" - VALIDATE_STATUS "+r.getProgramParameter(x,r.VALIDATE_STATUS)+`

Material Name: `+T.name+`
Material Type: `+T.type+`

Program Info Log: `+k+`
`+de+`
`+Ae)}else k!==""?console.warn("THREE.WebGLProgram: Program Info Log:",k):(G===""||K==="")&&(se=!1);se&&(T.diagnostics={runnable:W,programLog:k,vertexShader:{log:G,prefix:m},fragmentShader:{log:K,prefix:f}})}r.deleteShader(C),r.deleteShader(A),N=new Sr(r,x),v=x0(r,x)}let N;this.getUniforms=function(){return N===void 0&&I(this),N};let v;this.getAttributes=function(){return v===void 0&&I(this),v};let b=t.rendererExtensionParallelShaderCompile===!1;return this.isReady=function(){return b===!1&&(b=r.getProgramParameter(x,l0)),b},this.destroy=function(){n.releaseStatesOfProgram(this),r.deleteProgram(x),this.program=void 0},this.type=t.shaderType,this.name=t.shaderName,this.id=c0++,this.cacheKey=e,this.usedTimes=1,this.program=x,this.vertexShader=C,this.fragmentShader=A,this}var R0=0,oc=class{constructor(){this.shaderCache=new Map,this.materialCache=new Map}update(e){let t=e.vertexShader,n=e.fragmentShader,r=this._getShaderStage(t),s=this._getShaderStage(n),a=this._getShaderCacheForMaterial(e);return a.has(r)===!1&&(a.add(r),r.usedTimes++),a.has(s)===!1&&(a.add(s),s.usedTimes++),this}remove(e){let t=this.materialCache.get(e);for(let n of t)n.usedTimes--,n.usedTimes===0&&this.shaderCache.delete(n.code);return this.materialCache.delete(e),this}getVertexShaderID(e){return this._getShaderStage(e.vertexShader).id}getFragmentShaderID(e){return this._getShaderStage(e.fragmentShader).id}dispose(){this.shaderCache.clear(),this.materialCache.clear()}_getShaderCacheForMaterial(e){let t=this.materialCache,n=t.get(e);return n===void 0&&(n=new Set,t.set(e,n)),n}_getShaderStage(e){let t=this.shaderCache,n=t.get(e);return n===void 0&&(n=new lc(e),t.set(e,n)),n}},lc=class{constructor(e){this.id=R0++,this.code=e,this.usedTimes=0}};function I0(i,e,t,n,r,s,a){let o=new Xr,c=new oc,l=new Set,u=[],d=r.logarithmicDepthBuffer,h=r.vertexTextures,p=r.precision,g={MeshDepthMaterial:"depth",MeshDistanceMaterial:"distanceRGBA",MeshNormalMaterial:"normal",MeshBasicMaterial:"basic",MeshLambertMaterial:"lambert",MeshPhongMaterial:"phong",MeshToonMaterial:"toon",MeshStandardMaterial:"physical",MeshPhysicalMaterial:"physical",MeshMatcapMaterial:"matcap",LineBasicMaterial:"basic",LineDashedMaterial:"dashed",PointsMaterial:"points",ShadowMaterial:"shadow",SpriteMaterial:"sprite"};function x(v){return l.add(v),v===0?"uv":`uv${v}`}function m(v,b,T,P,U){let F=P.fog,k=U.geometry,G=v.isMeshStandardMaterial?P.environment:null,K=(v.isMeshStandardMaterial?t:e).get(v.envMap||G),W=K&&K.mapping===fs?K.image.height:null,se=g[v.type];v.precision!==null&&(p=r.getMaxPrecision(v.precision),p!==v.precision&&console.warn("THREE.WebGLProgram.getParameters:",v.precision,"not supported, using",p,"instead."));let de=k.morphAttributes.position||k.morphAttributes.normal||k.morphAttributes.color,Ae=de!==void 0?de.length:0,fe=0;k.morphAttributes.position!==void 0&&(fe=1),k.morphAttributes.normal!==void 0&&(fe=2),k.morphAttributes.color!==void 0&&(fe=3);let Oe,$e,Pe,X;if(se){let Qe=Dn[se];Oe=Qe.vertexShader,$e=Qe.fragmentShader}else Oe=v.vertexShader,$e=v.fragmentShader,c.update(v),Pe=c.getVertexShaderID(v),X=c.getFragmentShaderID(v);let J=i.getRenderTarget(),Y=i.state.buffers.depth.getReversed(),ae=U.isInstancedMesh===!0,pe=U.isBatchedMesh===!0,Ce=!!v.map,it=!!v.matcap,R=!!K,qe=!!v.aoMap,ue=!!v.lightMap,ye=!!v.bumpMap,le=!!v.normalMap,Je=!!v.displacementMap,_e=!!v.emissiveMap,He=!!v.metalnessMap,Re=!!v.roughnessMap,Ve=v.anisotropy>0,E=v.clearcoat>0,_=v.dispersion>0,z=v.iridescence>0,q=v.sheen>0,j=v.transmission>0,$=Ve&&!!v.anisotropyMap,Se=E&&!!v.clearcoatMap,re=E&&!!v.clearcoatNormalMap,be=E&&!!v.clearcoatRoughnessMap,we=z&&!!v.iridescenceMap,ee=z&&!!v.iridescenceThicknessMap,ge=q&&!!v.sheenColorMap,Fe=q&&!!v.sheenRoughnessMap,Ie=!!v.specularMap,he=!!v.specularColorMap,Ge=!!v.specularIntensityMap,L=j&&!!v.transmissionMap,ie=j&&!!v.thicknessMap,oe=!!v.gradientMap,Me=!!v.alphaMap,te=v.alphaTest>0,Z=!!v.alphaHash,Te=!!v.extensions,ze=qn;v.toneMapped&&(J===null||J.isXRRenderTarget===!0)&&(ze=i.toneMapping);let ot={shaderID:se,shaderType:v.type,shaderName:v.name,vertexShader:Oe,fragmentShader:$e,defines:v.defines,customVertexShaderID:Pe,customFragmentShaderID:X,isRawShaderMaterial:v.isRawShaderMaterial===!0,glslVersion:v.glslVersion,precision:p,batching:pe,batchingColor:pe&&U._colorsTexture!==null,instancing:ae,instancingColor:ae&&U.instanceColor!==null,instancingMorph:ae&&U.morphTexture!==null,supportsVertexTextures:h,outputColorSpace:J===null?i.outputColorSpace:J.isXRRenderTarget===!0?J.texture.colorSpace:Ti,alphaToCoverage:!!v.alphaToCoverage,map:Ce,matcap:it,envMap:R,envMapMode:R&&K.mapping,envMapCubeUVHeight:W,aoMap:qe,lightMap:ue,bumpMap:ye,normalMap:le,displacementMap:h&&Je,emissiveMap:_e,normalMapObjectSpace:le&&v.normalMapType===Yd,normalMapTangentSpace:le&&v.normalMapType===Vl,metalnessMap:He,roughnessMap:Re,anisotropy:Ve,anisotropyMap:$,clearcoat:E,clearcoatMap:Se,clearcoatNormalMap:re,clearcoatRoughnessMap:be,dispersion:_,iridescence:z,iridescenceMap:we,iridescenceThicknessMap:ee,sheen:q,sheenColorMap:ge,sheenRoughnessMap:Fe,specularMap:Ie,specularColorMap:he,specularIntensityMap:Ge,transmission:j,transmissionMap:L,thicknessMap:ie,gradientMap:oe,opaque:v.transparent===!1&&v.blending===Si&&v.alphaToCoverage===!1,alphaMap:Me,alphaTest:te,alphaHash:Z,combine:v.combine,mapUv:Ce&&x(v.map.channel),aoMapUv:qe&&x(v.aoMap.channel),lightMapUv:ue&&x(v.lightMap.channel),bumpMapUv:ye&&x(v.bumpMap.channel),normalMapUv:le&&x(v.normalMap.channel),displacementMapUv:Je&&x(v.displacementMap.channel),emissiveMapUv:_e&&x(v.emissiveMap.channel),metalnessMapUv:He&&x(v.metalnessMap.channel),roughnessMapUv:Re&&x(v.roughnessMap.channel),anisotropyMapUv:$&&x(v.anisotropyMap.channel),clearcoatMapUv:Se&&x(v.clearcoatMap.channel),clearcoatNormalMapUv:re&&x(v.clearcoatNormalMap.channel),clearcoatRoughnessMapUv:be&&x(v.clearcoatRoughnessMap.channel),iridescenceMapUv:we&&x(v.iridescenceMap.channel),iridescenceThicknessMapUv:ee&&x(v.iridescenceThicknessMap.channel),sheenColorMapUv:ge&&x(v.sheenColorMap.channel),sheenRoughnessMapUv:Fe&&x(v.sheenRoughnessMap.channel),specularMapUv:Ie&&x(v.specularMap.channel),specularColorMapUv:he&&x(v.specularColorMap.channel),specularIntensityMapUv:Ge&&x(v.specularIntensityMap.channel),transmissionMapUv:L&&x(v.transmissionMap.channel),thicknessMapUv:ie&&x(v.thicknessMap.channel),alphaMapUv:Me&&x(v.alphaMap.channel),vertexTangents:!!k.attributes.tangent&&(le||Ve),vertexColors:v.vertexColors,vertexAlphas:v.vertexColors===!0&&!!k.attributes.color&&k.attributes.color.itemSize===4,pointsUvs:U.isPoints===!0&&!!k.attributes.uv&&(Ce||Me),fog:!!F,useFog:v.fog===!0,fogExp2:!!F&&F.isFogExp2,flatShading:v.flatShading===!0&&v.wireframe===!1,sizeAttenuation:v.sizeAttenuation===!0,logarithmicDepthBuffer:d,reversedDepthBuffer:Y,skinning:U.isSkinnedMesh===!0,morphTargets:k.morphAttributes.position!==void 0,morphNormals:k.morphAttributes.normal!==void 0,morphColors:k.morphAttributes.color!==void 0,morphTargetsCount:Ae,morphTextureStride:fe,numDirLights:b.directional.length,numPointLights:b.point.length,numSpotLights:b.spot.length,numSpotLightMaps:b.spotLightMap.length,numRectAreaLights:b.rectArea.length,numHemiLights:b.hemi.length,numDirLightShadows:b.directionalShadowMap.length,numPointLightShadows:b.pointShadowMap.length,numSpotLightShadows:b.spotShadowMap.length,numSpotLightShadowsWithMaps:b.numSpotLightShadowsWithMaps,numLightProbes:b.numLightProbes,numClippingPlanes:a.numPlanes,numClipIntersection:a.numIntersection,dithering:v.dithering,shadowMapEnabled:i.shadowMap.enabled&&T.length>0,shadowMapType:i.shadowMap.type,toneMapping:ze,decodeVideoTexture:Ce&&v.map.isVideoTexture===!0&&Ke.getTransfer(v.map.colorSpace)===tt,decodeVideoTextureEmissive:_e&&v.emissiveMap.isVideoTexture===!0&&Ke.getTransfer(v.emissiveMap.colorSpace)===tt,premultipliedAlpha:v.premultipliedAlpha,doubleSided:v.side===un,flipSided:v.side===zt,useDepthPacking:v.depthPacking>=0,depthPacking:v.depthPacking||0,index0AttributeName:v.index0AttributeName,extensionClipCullDistance:Te&&v.extensions.clipCullDistance===!0&&n.has("WEBGL_clip_cull_distance"),extensionMultiDraw:(Te&&v.extensions.multiDraw===!0||pe)&&n.has("WEBGL_multi_draw"),rendererExtensionParallelShaderCompile:n.has("KHR_parallel_shader_compile"),customProgramCacheKey:v.customProgramCacheKey()};return ot.vertexUv1s=l.has(1),ot.vertexUv2s=l.has(2),ot.vertexUv3s=l.has(3),l.clear(),ot}function f(v){let b=[];if(v.shaderID?b.push(v.shaderID):(b.push(v.customVertexShaderID),b.push(v.customFragmentShaderID)),v.defines!==void 0)for(let T in v.defines)b.push(T),b.push(v.defines[T]);return v.isRawShaderMaterial===!1&&(S(b,v),M(b,v),b.push(i.outputColorSpace)),b.push(v.customProgramCacheKey),b.join()}function S(v,b){v.push(b.precision),v.push(b.outputColorSpace),v.push(b.envMapMode),v.push(b.envMapCubeUVHeight),v.push(b.mapUv),v.push(b.alphaMapUv),v.push(b.lightMapUv),v.push(b.aoMapUv),v.push(b.bumpMapUv),v.push(b.normalMapUv),v.push(b.displacementMapUv),v.push(b.emissiveMapUv),v.push(b.metalnessMapUv),v.push(b.roughnessMapUv),v.push(b.anisotropyMapUv),v.push(b.clearcoatMapUv),v.push(b.clearcoatNormalMapUv),v.push(b.clearcoatRoughnessMapUv),v.push(b.iridescenceMapUv),v.push(b.iridescenceThicknessMapUv),v.push(b.sheenColorMapUv),v.push(b.sheenRoughnessMapUv),v.push(b.specularMapUv),v.push(b.specularColorMapUv),v.push(b.specularIntensityMapUv),v.push(b.transmissionMapUv),v.push(b.thicknessMapUv),v.push(b.combine),v.push(b.fogExp2),v.push(b.sizeAttenuation),v.push(b.morphTargetsCount),v.push(b.morphAttributeCount),v.push(b.numDirLights),v.push(b.numPointLights),v.push(b.numSpotLights),v.push(b.numSpotLightMaps),v.push(b.numHemiLights),v.push(b.numRectAreaLights),v.push(b.numDirLightShadows),v.push(b.numPointLightShadows),v.push(b.numSpotLightShadows),v.push(b.numSpotLightShadowsWithMaps),v.push(b.numLightProbes),v.push(b.shadowMapType),v.push(b.toneMapping),v.push(b.numClippingPlanes),v.push(b.numClipIntersection),v.push(b.depthPacking)}function M(v,b){o.disableAll(),b.supportsVertexTextures&&o.enable(0),b.instancing&&o.enable(1),b.instancingColor&&o.enable(2),b.instancingMorph&&o.enable(3),b.matcap&&o.enable(4),b.envMap&&o.enable(5),b.normalMapObjectSpace&&o.enable(6),b.normalMapTangentSpace&&o.enable(7),b.clearcoat&&o.enable(8),b.iridescence&&o.enable(9),b.alphaTest&&o.enable(10),b.vertexColors&&o.enable(11),b.vertexAlphas&&o.enable(12),b.vertexUv1s&&o.enable(13),b.vertexUv2s&&o.enable(14),b.vertexUv3s&&o.enable(15),b.vertexTangents&&o.enable(16),b.anisotropy&&o.enable(17),b.alphaHash&&o.enable(18),b.batching&&o.enable(19),b.dispersion&&o.enable(20),b.batchingColor&&o.enable(21),b.gradientMap&&o.enable(22),v.push(o.mask),o.disableAll(),b.fog&&o.enable(0),b.useFog&&o.enable(1),b.flatShading&&o.enable(2),b.logarithmicDepthBuffer&&o.enable(3),b.reversedDepthBuffer&&o.enable(4),b.skinning&&o.enable(5),b.morphTargets&&o.enable(6),b.morphNormals&&o.enable(7),b.morphColors&&o.enable(8),b.premultipliedAlpha&&o.enable(9),b.shadowMapEnabled&&o.enable(10),b.doubleSided&&o.enable(11),b.flipSided&&o.enable(12),b.useDepthPacking&&o.enable(13),b.dithering&&o.enable(14),b.transmission&&o.enable(15),b.sheen&&o.enable(16),b.opaque&&o.enable(17),b.pointsUvs&&o.enable(18),b.decodeVideoTexture&&o.enable(19),b.decodeVideoTextureEmissive&&o.enable(20),b.alphaToCoverage&&o.enable(21),v.push(o.mask)}function y(v){let b=g[v.type],T;if(b){let P=Dn[b];T=su.clone(P.uniforms)}else T=v.uniforms;return T}function C(v,b){let T;for(let P=0,U=u.length;P<U;P++){let F=u[P];if(F.cacheKey===b){T=F,++T.usedTimes;break}}return T===void 0&&(T=new C0(i,b,v,s),u.push(T)),T}function A(v){if(--v.usedTimes===0){let b=u.indexOf(v);u[b]=u[u.length-1],u.pop(),v.destroy()}}function I(v){c.remove(v)}function N(){c.dispose()}return{getParameters:m,getProgramCacheKey:f,getUniforms:y,acquireProgram:C,releaseProgram:A,releaseShaderCache:I,programs:u,dispose:N}}function P0(){let i=new WeakMap;function e(a){return i.has(a)}function t(a){let o=i.get(a);return o===void 0&&(o={},i.set(a,o)),o}function n(a){i.delete(a)}function r(a,o,c){i.get(a)[o]=c}function s(){i=new WeakMap}return{has:e,get:t,remove:n,update:r,dispose:s}}function N0(i,e){return i.groupOrder!==e.groupOrder?i.groupOrder-e.groupOrder:i.renderOrder!==e.renderOrder?i.renderOrder-e.renderOrder:i.material.id!==e.material.id?i.material.id-e.material.id:i.z!==e.z?i.z-e.z:i.id-e.id}function Cu(i,e){return i.groupOrder!==e.groupOrder?i.groupOrder-e.groupOrder:i.renderOrder!==e.renderOrder?i.renderOrder-e.renderOrder:i.z!==e.z?e.z-i.z:i.id-e.id}function Ru(){let i=[],e=0,t=[],n=[],r=[];function s(){e=0,t.length=0,n.length=0,r.length=0}function a(d,h,p,g,x,m){let f=i[e];return f===void 0?(f={id:d.id,object:d,geometry:h,material:p,groupOrder:g,renderOrder:d.renderOrder,z:x,group:m},i[e]=f):(f.id=d.id,f.object=d,f.geometry=h,f.material=p,f.groupOrder=g,f.renderOrder=d.renderOrder,f.z=x,f.group=m),e++,f}function o(d,h,p,g,x,m){let f=a(d,h,p,g,x,m);p.transmission>0?n.push(f):p.transparent===!0?r.push(f):t.push(f)}function c(d,h,p,g,x,m){let f=a(d,h,p,g,x,m);p.transmission>0?n.unshift(f):p.transparent===!0?r.unshift(f):t.unshift(f)}function l(d,h){t.length>1&&t.sort(d||N0),n.length>1&&n.sort(h||Cu),r.length>1&&r.sort(h||Cu)}function u(){for(let d=e,h=i.length;d<h;d++){let p=i[d];if(p.id===null)break;p.id=null,p.object=null,p.geometry=null,p.material=null,p.group=null}}return{opaque:t,transmissive:n,transparent:r,init:s,push:o,unshift:c,finish:u,sort:l}}function D0(){let i=new WeakMap;function e(n,r){let s=i.get(n),a;return s===void 0?(a=new Ru,i.set(n,[a])):r>=s.length?(a=new Ru,s.push(a)):a=s[r],a}function t(){i=new WeakMap}return{get:e,dispose:t}}function L0(){let i={};return{get:function(e){if(i[e.id]!==void 0)return i[e.id];let t;switch(e.type){case"DirectionalLight":t={direction:new D,color:new Be};break;case"SpotLight":t={position:new D,direction:new D,color:new Be,distance:0,coneCos:0,penumbraCos:0,decay:0};break;case"PointLight":t={position:new D,color:new Be,distance:0,decay:0};break;case"HemisphereLight":t={direction:new D,skyColor:new Be,groundColor:new Be};break;case"RectAreaLight":t={color:new Be,position:new D,halfWidth:new D,halfHeight:new D};break}return i[e.id]=t,t}}}function F0(){let i={};return{get:function(e){if(i[e.id]!==void 0)return i[e.id];let t;switch(e.type){case"DirectionalLight":t={shadowIntensity:1,shadowBias:0,shadowNormalBias:0,shadowRadius:1,shadowMapSize:new We};break;case"SpotLight":t={shadowIntensity:1,shadowBias:0,shadowNormalBias:0,shadowRadius:1,shadowMapSize:new We};break;case"PointLight":t={shadowIntensity:1,shadowBias:0,shadowNormalBias:0,shadowRadius:1,shadowMapSize:new We,shadowCameraNear:1,shadowCameraFar:1e3};break}return i[e.id]=t,t}}}var U0=0;function O0(i,e){return(e.castShadow?2:0)-(i.castShadow?2:0)+(e.map?1:0)-(i.map?1:0)}function B0(i){let e=new L0,t=F0(),n={version:0,hash:{directionalLength:-1,pointLength:-1,spotLength:-1,rectAreaLength:-1,hemiLength:-1,numDirectionalShadows:-1,numPointShadows:-1,numSpotShadows:-1,numSpotMaps:-1,numLightProbes:-1},ambient:[0,0,0],probe:[],directional:[],directionalShadow:[],directionalShadowMap:[],directionalShadowMatrix:[],spot:[],spotLightMap:[],spotShadow:[],spotShadowMap:[],spotLightMatrix:[],rectArea:[],rectAreaLTC1:null,rectAreaLTC2:null,point:[],pointShadow:[],pointShadowMap:[],pointShadowMatrix:[],hemi:[],numSpotLightShadowsWithMaps:0,numLightProbes:0};for(let l=0;l<9;l++)n.probe.push(new D);let r=new D,s=new ht,a=new ht;function o(l){let u=0,d=0,h=0;for(let v=0;v<9;v++)n.probe[v].set(0,0,0);let p=0,g=0,x=0,m=0,f=0,S=0,M=0,y=0,C=0,A=0,I=0;l.sort(O0);for(let v=0,b=l.length;v<b;v++){let T=l[v],P=T.color,U=T.intensity,F=T.distance,k=T.shadow&&T.shadow.map?T.shadow.map.texture:null;if(T.isAmbientLight)u+=P.r*U,d+=P.g*U,h+=P.b*U;else if(T.isLightProbe){for(let G=0;G<9;G++)n.probe[G].addScaledVector(T.sh.coefficients[G],U);I++}else if(T.isDirectionalLight){let G=e.get(T);if(G.color.copy(T.color).multiplyScalar(T.intensity),T.castShadow){let K=T.shadow,W=t.get(T);W.shadowIntensity=K.intensity,W.shadowBias=K.bias,W.shadowNormalBias=K.normalBias,W.shadowRadius=K.radius,W.shadowMapSize=K.mapSize,n.directionalShadow[p]=W,n.directionalShadowMap[p]=k,n.directionalShadowMatrix[p]=T.shadow.matrix,S++}n.directional[p]=G,p++}else if(T.isSpotLight){let G=e.get(T);G.position.setFromMatrixPosition(T.matrixWorld),G.color.copy(P).multiplyScalar(U),G.distance=F,G.coneCos=Math.cos(T.angle),G.penumbraCos=Math.cos(T.angle*(1-T.penumbra)),G.decay=T.decay,n.spot[x]=G;let K=T.shadow;if(T.map&&(n.spotLightMap[C]=T.map,C++,K.updateMatrices(T),T.castShadow&&A++),n.spotLightMatrix[x]=K.matrix,T.castShadow){let W=t.get(T);W.shadowIntensity=K.intensity,W.shadowBias=K.bias,W.shadowNormalBias=K.normalBias,W.shadowRadius=K.radius,W.shadowMapSize=K.mapSize,n.spotShadow[x]=W,n.spotShadowMap[x]=k,y++}x++}else if(T.isRectAreaLight){let G=e.get(T);G.color.copy(P).multiplyScalar(U),G.halfWidth.set(T.width*.5,0,0),G.halfHeight.set(0,T.height*.5,0),n.rectArea[m]=G,m++}else if(T.isPointLight){let G=e.get(T);if(G.color.copy(T.color).multiplyScalar(T.intensity),G.distance=T.distance,G.decay=T.decay,T.castShadow){let K=T.shadow,W=t.get(T);W.shadowIntensity=K.intensity,W.shadowBias=K.bias,W.shadowNormalBias=K.normalBias,W.shadowRadius=K.radius,W.shadowMapSize=K.mapSize,W.shadowCameraNear=K.camera.near,W.shadowCameraFar=K.camera.far,n.pointShadow[g]=W,n.pointShadowMap[g]=k,n.pointShadowMatrix[g]=T.shadow.matrix,M++}n.point[g]=G,g++}else if(T.isHemisphereLight){let G=e.get(T);G.skyColor.copy(T.color).multiplyScalar(U),G.groundColor.copy(T.groundColor).multiplyScalar(U),n.hemi[f]=G,f++}}m>0&&(i.has("OES_texture_float_linear")===!0?(n.rectAreaLTC1=ce.LTC_FLOAT_1,n.rectAreaLTC2=ce.LTC_FLOAT_2):(n.rectAreaLTC1=ce.LTC_HALF_1,n.rectAreaLTC2=ce.LTC_HALF_2)),n.ambient[0]=u,n.ambient[1]=d,n.ambient[2]=h;let N=n.hash;(N.directionalLength!==p||N.pointLength!==g||N.spotLength!==x||N.rectAreaLength!==m||N.hemiLength!==f||N.numDirectionalShadows!==S||N.numPointShadows!==M||N.numSpotShadows!==y||N.numSpotMaps!==C||N.numLightProbes!==I)&&(n.directional.length=p,n.spot.length=x,n.rectArea.length=m,n.point.length=g,n.hemi.length=f,n.directionalShadow.length=S,n.directionalShadowMap.length=S,n.pointShadow.length=M,n.pointShadowMap.length=M,n.spotShadow.length=y,n.spotShadowMap.length=y,n.directionalShadowMatrix.length=S,n.pointShadowMatrix.length=M,n.spotLightMatrix.length=y+C-A,n.spotLightMap.length=C,n.numSpotLightShadowsWithMaps=A,n.numLightProbes=I,N.directionalLength=p,N.pointLength=g,N.spotLength=x,N.rectAreaLength=m,N.hemiLength=f,N.numDirectionalShadows=S,N.numPointShadows=M,N.numSpotShadows=y,N.numSpotMaps=C,N.numLightProbes=I,n.version=U0++)}function c(l,u){let d=0,h=0,p=0,g=0,x=0,m=u.matrixWorldInverse;for(let f=0,S=l.length;f<S;f++){let M=l[f];if(M.isDirectionalLight){let y=n.directional[d];y.direction.setFromMatrixPosition(M.matrixWorld),r.setFromMatrixPosition(M.target.matrixWorld),y.direction.sub(r),y.direction.transformDirection(m),d++}else if(M.isSpotLight){let y=n.spot[p];y.position.setFromMatrixPosition(M.matrixWorld),y.position.applyMatrix4(m),y.direction.setFromMatrixPosition(M.matrixWorld),r.setFromMatrixPosition(M.target.matrixWorld),y.direction.sub(r),y.direction.transformDirection(m),p++}else if(M.isRectAreaLight){let y=n.rectArea[g];y.position.setFromMatrixPosition(M.matrixWorld),y.position.applyMatrix4(m),a.identity(),s.copy(M.matrixWorld),s.premultiply(m),a.extractRotation(s),y.halfWidth.set(M.width*.5,0,0),y.halfHeight.set(0,M.height*.5,0),y.halfWidth.applyMatrix4(a),y.halfHeight.applyMatrix4(a),g++}else if(M.isPointLight){let y=n.point[h];y.position.setFromMatrixPosition(M.matrixWorld),y.position.applyMatrix4(m),h++}else if(M.isHemisphereLight){let y=n.hemi[x];y.direction.setFromMatrixPosition(M.matrixWorld),y.direction.transformDirection(m),x++}}}return{setup:o,setupView:c,state:n}}function Iu(i){let e=new B0(i),t=[],n=[];function r(u){l.camera=u,t.length=0,n.length=0}function s(u){t.push(u)}function a(u){n.push(u)}function o(){e.setup(t)}function c(u){e.setupView(t,u)}let l={lightsArray:t,shadowsArray:n,camera:null,lights:e,transmissionRenderTarget:{}};return{init:r,state:l,setupLights:o,setupLightsView:c,pushLight:s,pushShadow:a}}function z0(i){let e=new WeakMap;function t(r,s=0){let a=e.get(r),o;return a===void 0?(o=new Iu(i),e.set(r,[o])):s>=a.length?(o=new Iu(i),a.push(o)):o=a[s],o}function n(){e=new WeakMap}return{get:t,dispose:n}}var k0=`void main() {
	gl_Position = vec4( position, 1.0 );
}`,H0=`uniform sampler2D shadow_pass;
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
}`;function V0(i,e,t){let n=new gr,r=new We,s=new We,a=new xt,o=new ba({depthPacking:qd}),c=new wa,l={},u=t.maxTextureSize,d={[Gn]:zt,[zt]:Gn,[un]:un},h=new tn({defines:{VSM_SAMPLES:8},uniforms:{shadow_pass:{value:null},resolution:{value:new We},radius:{value:4}},vertexShader:k0,fragmentShader:H0}),p=h.clone();p.defines.HORIZONTAL_PASS=1;let g=new ft;g.setAttribute("position",new Vt(new Float32Array([-1,-1,.5,3,-1,.5,-1,3,.5]),3));let x=new dt(g,h),m=this;this.enabled=!1,this.autoUpdate=!0,this.needsUpdate=!1,this.type=Cl;let f=this.type;this.render=function(A,I,N){if(m.enabled===!1||m.autoUpdate===!1&&m.needsUpdate===!1||A.length===0)return;let v=i.getRenderTarget(),b=i.getActiveCubeFace(),T=i.getActiveMipmapLevel(),P=i.state;P.setBlending($n),P.buffers.depth.getReversed()===!0?P.buffers.color.setClear(0,0,0,0):P.buffers.color.setClear(1,1,1,1),P.buffers.depth.setTest(!0),P.setScissorTest(!1);let U=f!==Pn&&this.type===Pn,F=f===Pn&&this.type!==Pn;for(let k=0,G=A.length;k<G;k++){let K=A[k],W=K.shadow;if(W===void 0){console.warn("THREE.WebGLShadowMap:",K,"has no shadow.");continue}if(W.autoUpdate===!1&&W.needsUpdate===!1)continue;r.copy(W.mapSize);let se=W.getFrameExtents();if(r.multiply(se),s.copy(W.mapSize),(r.x>u||r.y>u)&&(r.x>u&&(s.x=Math.floor(u/se.x),r.x=s.x*se.x,W.mapSize.x=s.x),r.y>u&&(s.y=Math.floor(u/se.y),r.y=s.y*se.y,W.mapSize.y=s.y)),W.map===null||U===!0||F===!0){let Ae=this.type!==Pn?{minFilter:dn,magFilter:dn}:{};W.map!==null&&W.map.dispose(),W.map=new Rn(r.x,r.y,Ae),W.map.texture.name=K.name+".shadowMap",W.camera.updateProjectionMatrix()}i.setRenderTarget(W.map),i.clear();let de=W.getViewportCount();for(let Ae=0;Ae<de;Ae++){let fe=W.getViewport(Ae);a.set(s.x*fe.x,s.y*fe.y,s.x*fe.z,s.y*fe.w),P.viewport(a),W.updateMatrices(K,Ae),n=W.getFrustum(),y(I,N,W.camera,K,this.type)}W.isPointLightShadow!==!0&&this.type===Pn&&S(W,N),W.needsUpdate=!1}f=this.type,m.needsUpdate=!1,i.setRenderTarget(v,b,T)};function S(A,I){let N=e.update(x);h.defines.VSM_SAMPLES!==A.blurSamples&&(h.defines.VSM_SAMPLES=A.blurSamples,p.defines.VSM_SAMPLES=A.blurSamples,h.needsUpdate=!0,p.needsUpdate=!0),A.mapPass===null&&(A.mapPass=new Rn(r.x,r.y)),h.uniforms.shadow_pass.value=A.map.texture,h.uniforms.resolution.value=A.mapSize,h.uniforms.radius.value=A.radius,i.setRenderTarget(A.mapPass),i.clear(),i.renderBufferDirect(I,null,N,h,x,null),p.uniforms.shadow_pass.value=A.mapPass.texture,p.uniforms.resolution.value=A.mapSize,p.uniforms.radius.value=A.radius,i.setRenderTarget(A.map),i.clear(),i.renderBufferDirect(I,null,N,p,x,null)}function M(A,I,N,v){let b=null,T=N.isPointLight===!0?A.customDistanceMaterial:A.customDepthMaterial;if(T!==void 0)b=T;else if(b=N.isPointLight===!0?c:o,i.localClippingEnabled&&I.clipShadows===!0&&Array.isArray(I.clippingPlanes)&&I.clippingPlanes.length!==0||I.displacementMap&&I.displacementScale!==0||I.alphaMap&&I.alphaTest>0||I.map&&I.alphaTest>0||I.alphaToCoverage===!0){let P=b.uuid,U=I.uuid,F=l[P];F===void 0&&(F={},l[P]=F);let k=F[U];k===void 0&&(k=b.clone(),F[U]=k,I.addEventListener("dispose",C)),b=k}if(b.visible=I.visible,b.wireframe=I.wireframe,v===Pn?b.side=I.shadowSide!==null?I.shadowSide:I.side:b.side=I.shadowSide!==null?I.shadowSide:d[I.side],b.alphaMap=I.alphaMap,b.alphaTest=I.alphaToCoverage===!0?.5:I.alphaTest,b.map=I.map,b.clipShadows=I.clipShadows,b.clippingPlanes=I.clippingPlanes,b.clipIntersection=I.clipIntersection,b.displacementMap=I.displacementMap,b.displacementScale=I.displacementScale,b.displacementBias=I.displacementBias,b.wireframeLinewidth=I.wireframeLinewidth,b.linewidth=I.linewidth,N.isPointLight===!0&&b.isMeshDistanceMaterial===!0){let P=i.properties.get(b);P.light=N}return b}function y(A,I,N,v,b){if(A.visible===!1)return;if(A.layers.test(I.layers)&&(A.isMesh||A.isLine||A.isPoints)&&(A.castShadow||A.receiveShadow&&b===Pn)&&(!A.frustumCulled||n.intersectsObject(A))){A.modelViewMatrix.multiplyMatrices(N.matrixWorldInverse,A.matrixWorld);let U=e.update(A),F=A.material;if(Array.isArray(F)){let k=U.groups;for(let G=0,K=k.length;G<K;G++){let W=k[G],se=F[W.materialIndex];if(se&&se.visible){let de=M(A,se,v,b);A.onBeforeShadow(i,A,I,N,U,de,W),i.renderBufferDirect(N,null,U,de,A,W),A.onAfterShadow(i,A,I,N,U,de,W)}}}else if(F.visible){let k=M(A,F,v,b);A.onBeforeShadow(i,A,I,N,U,k,null),i.renderBufferDirect(N,null,U,k,A,null),A.onAfterShadow(i,A,I,N,U,k,null)}}let P=A.children;for(let U=0,F=P.length;U<F;U++)y(P[U],I,N,v,b)}function C(A){A.target.removeEventListener("dispose",C);for(let N in l){let v=l[N],b=A.target.uuid;b in v&&(v[b].dispose(),delete v[b])}}}var G0={[Da]:La,[Fa]:Ba,[Ua]:za,[Ei]:Oa,[La]:Da,[Ba]:Fa,[za]:Ua,[Oa]:Ei};function W0(i,e){function t(){let L=!1,ie=new xt,oe=null,Me=new xt(0,0,0,0);return{setMask:function(te){oe!==te&&!L&&(i.colorMask(te,te,te,te),oe=te)},setLocked:function(te){L=te},setClear:function(te,Z,Te,ze,ot){ot===!0&&(te*=ze,Z*=ze,Te*=ze),ie.set(te,Z,Te,ze),Me.equals(ie)===!1&&(i.clearColor(te,Z,Te,ze),Me.copy(ie))},reset:function(){L=!1,oe=null,Me.set(-1,0,0,0)}}}function n(){let L=!1,ie=!1,oe=null,Me=null,te=null;return{setReversed:function(Z){if(ie!==Z){let Te=e.get("EXT_clip_control");Z?Te.clipControlEXT(Te.LOWER_LEFT_EXT,Te.ZERO_TO_ONE_EXT):Te.clipControlEXT(Te.LOWER_LEFT_EXT,Te.NEGATIVE_ONE_TO_ONE_EXT),ie=Z;let ze=te;te=null,this.setClear(ze)}},getReversed:function(){return ie},setTest:function(Z){Z?J(i.DEPTH_TEST):Y(i.DEPTH_TEST)},setMask:function(Z){oe!==Z&&!L&&(i.depthMask(Z),oe=Z)},setFunc:function(Z){if(ie&&(Z=G0[Z]),Me!==Z){switch(Z){case Da:i.depthFunc(i.NEVER);break;case La:i.depthFunc(i.ALWAYS);break;case Fa:i.depthFunc(i.LESS);break;case Ei:i.depthFunc(i.LEQUAL);break;case Ua:i.depthFunc(i.EQUAL);break;case Oa:i.depthFunc(i.GEQUAL);break;case Ba:i.depthFunc(i.GREATER);break;case za:i.depthFunc(i.NOTEQUAL);break;default:i.depthFunc(i.LEQUAL)}Me=Z}},setLocked:function(Z){L=Z},setClear:function(Z){te!==Z&&(ie&&(Z=1-Z),i.clearDepth(Z),te=Z)},reset:function(){L=!1,oe=null,Me=null,te=null,ie=!1}}}function r(){let L=!1,ie=null,oe=null,Me=null,te=null,Z=null,Te=null,ze=null,ot=null;return{setTest:function(Qe){L||(Qe?J(i.STENCIL_TEST):Y(i.STENCIL_TEST))},setMask:function(Qe){ie!==Qe&&!L&&(i.stencilMask(Qe),ie=Qe)},setFunc:function(Qe,Fn,Tn){(oe!==Qe||Me!==Fn||te!==Tn)&&(i.stencilFunc(Qe,Fn,Tn),oe=Qe,Me=Fn,te=Tn)},setOp:function(Qe,Fn,Tn){(Z!==Qe||Te!==Fn||ze!==Tn)&&(i.stencilOp(Qe,Fn,Tn),Z=Qe,Te=Fn,ze=Tn)},setLocked:function(Qe){L=Qe},setClear:function(Qe){ot!==Qe&&(i.clearStencil(Qe),ot=Qe)},reset:function(){L=!1,ie=null,oe=null,Me=null,te=null,Z=null,Te=null,ze=null,ot=null}}}let s=new t,a=new n,o=new r,c=new WeakMap,l=new WeakMap,u={},d={},h=new WeakMap,p=[],g=null,x=!1,m=null,f=null,S=null,M=null,y=null,C=null,A=null,I=new Be(0,0,0),N=0,v=!1,b=null,T=null,P=null,U=null,F=null,k=i.getParameter(i.MAX_COMBINED_TEXTURE_IMAGE_UNITS),G=!1,K=0,W=i.getParameter(i.VERSION);W.indexOf("WebGL")!==-1?(K=parseFloat(/^WebGL (\d)/.exec(W)[1]),G=K>=1):W.indexOf("OpenGL ES")!==-1&&(K=parseFloat(/^OpenGL ES (\d)/.exec(W)[1]),G=K>=2);let se=null,de={},Ae=i.getParameter(i.SCISSOR_BOX),fe=i.getParameter(i.VIEWPORT),Oe=new xt().fromArray(Ae),$e=new xt().fromArray(fe);function Pe(L,ie,oe,Me){let te=new Uint8Array(4),Z=i.createTexture();i.bindTexture(L,Z),i.texParameteri(L,i.TEXTURE_MIN_FILTER,i.NEAREST),i.texParameteri(L,i.TEXTURE_MAG_FILTER,i.NEAREST);for(let Te=0;Te<oe;Te++)L===i.TEXTURE_3D||L===i.TEXTURE_2D_ARRAY?i.texImage3D(ie,0,i.RGBA,1,1,Me,0,i.RGBA,i.UNSIGNED_BYTE,te):i.texImage2D(ie+Te,0,i.RGBA,1,1,0,i.RGBA,i.UNSIGNED_BYTE,te);return Z}let X={};X[i.TEXTURE_2D]=Pe(i.TEXTURE_2D,i.TEXTURE_2D,1),X[i.TEXTURE_CUBE_MAP]=Pe(i.TEXTURE_CUBE_MAP,i.TEXTURE_CUBE_MAP_POSITIVE_X,6),X[i.TEXTURE_2D_ARRAY]=Pe(i.TEXTURE_2D_ARRAY,i.TEXTURE_2D_ARRAY,1,1),X[i.TEXTURE_3D]=Pe(i.TEXTURE_3D,i.TEXTURE_3D,1,1),s.setClear(0,0,0,1),a.setClear(1),o.setClear(0),J(i.DEPTH_TEST),a.setFunc(Ei),ye(!1),le(Al),J(i.CULL_FACE),qe($n);function J(L){u[L]!==!0&&(i.enable(L),u[L]=!0)}function Y(L){u[L]!==!1&&(i.disable(L),u[L]=!1)}function ae(L,ie){return d[L]!==ie?(i.bindFramebuffer(L,ie),d[L]=ie,L===i.DRAW_FRAMEBUFFER&&(d[i.FRAMEBUFFER]=ie),L===i.FRAMEBUFFER&&(d[i.DRAW_FRAMEBUFFER]=ie),!0):!1}function pe(L,ie){let oe=p,Me=!1;if(L){oe=h.get(ie),oe===void 0&&(oe=[],h.set(ie,oe));let te=L.textures;if(oe.length!==te.length||oe[0]!==i.COLOR_ATTACHMENT0){for(let Z=0,Te=te.length;Z<Te;Z++)oe[Z]=i.COLOR_ATTACHMENT0+Z;oe.length=te.length,Me=!0}}else oe[0]!==i.BACK&&(oe[0]=i.BACK,Me=!0);Me&&i.drawBuffers(oe)}function Ce(L){return g!==L?(i.useProgram(L),g=L,!0):!1}let it={[ai]:i.FUNC_ADD,[yd]:i.FUNC_SUBTRACT,[vd]:i.FUNC_REVERSE_SUBTRACT};it[bd]=i.MIN,it[wd]=i.MAX;let R={[Md]:i.ZERO,[Sd]:i.ONE,[Ed]:i.SRC_COLOR,[aa]:i.SRC_ALPHA,[Pd]:i.SRC_ALPHA_SATURATE,[Rd]:i.DST_COLOR,[Ad]:i.DST_ALPHA,[Td]:i.ONE_MINUS_SRC_COLOR,[oa]:i.ONE_MINUS_SRC_ALPHA,[Id]:i.ONE_MINUS_DST_COLOR,[Cd]:i.ONE_MINUS_DST_ALPHA,[Nd]:i.CONSTANT_COLOR,[Dd]:i.ONE_MINUS_CONSTANT_COLOR,[Ld]:i.CONSTANT_ALPHA,[Fd]:i.ONE_MINUS_CONSTANT_ALPHA};function qe(L,ie,oe,Me,te,Z,Te,ze,ot,Qe){if(L===$n){x===!0&&(Y(i.BLEND),x=!1);return}if(x===!1&&(J(i.BLEND),x=!0),L!==_d){if(L!==m||Qe!==v){if((f!==ai||y!==ai)&&(i.blendEquation(i.FUNC_ADD),f=ai,y=ai),Qe)switch(L){case Si:i.blendFuncSeparate(i.ONE,i.ONE_MINUS_SRC_ALPHA,i.ONE,i.ONE_MINUS_SRC_ALPHA);break;case Rl:i.blendFunc(i.ONE,i.ONE);break;case Il:i.blendFuncSeparate(i.ZERO,i.ONE_MINUS_SRC_COLOR,i.ZERO,i.ONE);break;case Pl:i.blendFuncSeparate(i.DST_COLOR,i.ONE_MINUS_SRC_ALPHA,i.ZERO,i.ONE);break;default:console.error("THREE.WebGLState: Invalid blending: ",L);break}else switch(L){case Si:i.blendFuncSeparate(i.SRC_ALPHA,i.ONE_MINUS_SRC_ALPHA,i.ONE,i.ONE_MINUS_SRC_ALPHA);break;case Rl:i.blendFuncSeparate(i.SRC_ALPHA,i.ONE,i.ONE,i.ONE);break;case Il:console.error("THREE.WebGLState: SubtractiveBlending requires material.premultipliedAlpha = true");break;case Pl:console.error("THREE.WebGLState: MultiplyBlending requires material.premultipliedAlpha = true");break;default:console.error("THREE.WebGLState: Invalid blending: ",L);break}S=null,M=null,C=null,A=null,I.set(0,0,0),N=0,m=L,v=Qe}return}te=te||ie,Z=Z||oe,Te=Te||Me,(ie!==f||te!==y)&&(i.blendEquationSeparate(it[ie],it[te]),f=ie,y=te),(oe!==S||Me!==M||Z!==C||Te!==A)&&(i.blendFuncSeparate(R[oe],R[Me],R[Z],R[Te]),S=oe,M=Me,C=Z,A=Te),(ze.equals(I)===!1||ot!==N)&&(i.blendColor(ze.r,ze.g,ze.b,ot),I.copy(ze),N=ot),m=L,v=!1}function ue(L,ie){L.side===un?Y(i.CULL_FACE):J(i.CULL_FACE);let oe=L.side===zt;ie&&(oe=!oe),ye(oe),L.blending===Si&&L.transparent===!1?qe($n):qe(L.blending,L.blendEquation,L.blendSrc,L.blendDst,L.blendEquationAlpha,L.blendSrcAlpha,L.blendDstAlpha,L.blendColor,L.blendAlpha,L.premultipliedAlpha),a.setFunc(L.depthFunc),a.setTest(L.depthTest),a.setMask(L.depthWrite),s.setMask(L.colorWrite);let Me=L.stencilWrite;o.setTest(Me),Me&&(o.setMask(L.stencilWriteMask),o.setFunc(L.stencilFunc,L.stencilRef,L.stencilFuncMask),o.setOp(L.stencilFail,L.stencilZFail,L.stencilZPass)),_e(L.polygonOffset,L.polygonOffsetFactor,L.polygonOffsetUnits),L.alphaToCoverage===!0?J(i.SAMPLE_ALPHA_TO_COVERAGE):Y(i.SAMPLE_ALPHA_TO_COVERAGE)}function ye(L){b!==L&&(L?i.frontFace(i.CW):i.frontFace(i.CCW),b=L)}function le(L){L!==md?(J(i.CULL_FACE),L!==T&&(L===Al?i.cullFace(i.BACK):L===gd?i.cullFace(i.FRONT):i.cullFace(i.FRONT_AND_BACK))):Y(i.CULL_FACE),T=L}function Je(L){L!==P&&(G&&i.lineWidth(L),P=L)}function _e(L,ie,oe){L?(J(i.POLYGON_OFFSET_FILL),(U!==ie||F!==oe)&&(i.polygonOffset(ie,oe),U=ie,F=oe)):Y(i.POLYGON_OFFSET_FILL)}function He(L){L?J(i.SCISSOR_TEST):Y(i.SCISSOR_TEST)}function Re(L){L===void 0&&(L=i.TEXTURE0+k-1),se!==L&&(i.activeTexture(L),se=L)}function Ve(L,ie,oe){oe===void 0&&(se===null?oe=i.TEXTURE0+k-1:oe=se);let Me=de[oe];Me===void 0&&(Me={type:void 0,texture:void 0},de[oe]=Me),(Me.type!==L||Me.texture!==ie)&&(se!==oe&&(i.activeTexture(oe),se=oe),i.bindTexture(L,ie||X[L]),Me.type=L,Me.texture=ie)}function E(){let L=de[se];L!==void 0&&L.type!==void 0&&(i.bindTexture(L.type,null),L.type=void 0,L.texture=void 0)}function _(){try{i.compressedTexImage2D(...arguments)}catch(L){console.error("THREE.WebGLState:",L)}}function z(){try{i.compressedTexImage3D(...arguments)}catch(L){console.error("THREE.WebGLState:",L)}}function q(){try{i.texSubImage2D(...arguments)}catch(L){console.error("THREE.WebGLState:",L)}}function j(){try{i.texSubImage3D(...arguments)}catch(L){console.error("THREE.WebGLState:",L)}}function $(){try{i.compressedTexSubImage2D(...arguments)}catch(L){console.error("THREE.WebGLState:",L)}}function Se(){try{i.compressedTexSubImage3D(...arguments)}catch(L){console.error("THREE.WebGLState:",L)}}function re(){try{i.texStorage2D(...arguments)}catch(L){console.error("THREE.WebGLState:",L)}}function be(){try{i.texStorage3D(...arguments)}catch(L){console.error("THREE.WebGLState:",L)}}function we(){try{i.texImage2D(...arguments)}catch(L){console.error("THREE.WebGLState:",L)}}function ee(){try{i.texImage3D(...arguments)}catch(L){console.error("THREE.WebGLState:",L)}}function ge(L){Oe.equals(L)===!1&&(i.scissor(L.x,L.y,L.z,L.w),Oe.copy(L))}function Fe(L){$e.equals(L)===!1&&(i.viewport(L.x,L.y,L.z,L.w),$e.copy(L))}function Ie(L,ie){let oe=l.get(ie);oe===void 0&&(oe=new WeakMap,l.set(ie,oe));let Me=oe.get(L);Me===void 0&&(Me=i.getUniformBlockIndex(ie,L.name),oe.set(L,Me))}function he(L,ie){let Me=l.get(ie).get(L);c.get(ie)!==Me&&(i.uniformBlockBinding(ie,Me,L.__bindingPointIndex),c.set(ie,Me))}function Ge(){i.disable(i.BLEND),i.disable(i.CULL_FACE),i.disable(i.DEPTH_TEST),i.disable(i.POLYGON_OFFSET_FILL),i.disable(i.SCISSOR_TEST),i.disable(i.STENCIL_TEST),i.disable(i.SAMPLE_ALPHA_TO_COVERAGE),i.blendEquation(i.FUNC_ADD),i.blendFunc(i.ONE,i.ZERO),i.blendFuncSeparate(i.ONE,i.ZERO,i.ONE,i.ZERO),i.blendColor(0,0,0,0),i.colorMask(!0,!0,!0,!0),i.clearColor(0,0,0,0),i.depthMask(!0),i.depthFunc(i.LESS),a.setReversed(!1),i.clearDepth(1),i.stencilMask(4294967295),i.stencilFunc(i.ALWAYS,0,4294967295),i.stencilOp(i.KEEP,i.KEEP,i.KEEP),i.clearStencil(0),i.cullFace(i.BACK),i.frontFace(i.CCW),i.polygonOffset(0,0),i.activeTexture(i.TEXTURE0),i.bindFramebuffer(i.FRAMEBUFFER,null),i.bindFramebuffer(i.DRAW_FRAMEBUFFER,null),i.bindFramebuffer(i.READ_FRAMEBUFFER,null),i.useProgram(null),i.lineWidth(1),i.scissor(0,0,i.canvas.width,i.canvas.height),i.viewport(0,0,i.canvas.width,i.canvas.height),u={},se=null,de={},d={},h=new WeakMap,p=[],g=null,x=!1,m=null,f=null,S=null,M=null,y=null,C=null,A=null,I=new Be(0,0,0),N=0,v=!1,b=null,T=null,P=null,U=null,F=null,Oe.set(0,0,i.canvas.width,i.canvas.height),$e.set(0,0,i.canvas.width,i.canvas.height),s.reset(),a.reset(),o.reset()}return{buffers:{color:s,depth:a,stencil:o},enable:J,disable:Y,bindFramebuffer:ae,drawBuffers:pe,useProgram:Ce,setBlending:qe,setMaterial:ue,setFlipSided:ye,setCullFace:le,setLineWidth:Je,setPolygonOffset:_e,setScissorTest:He,activeTexture:Re,bindTexture:Ve,unbindTexture:E,compressedTexImage2D:_,compressedTexImage3D:z,texImage2D:we,texImage3D:ee,updateUBOMapping:Ie,uniformBlockBinding:he,texStorage2D:re,texStorage3D:be,texSubImage2D:q,texSubImage3D:j,compressedTexSubImage2D:$,compressedTexSubImage3D:Se,scissor:ge,viewport:Fe,reset:Ge}}function X0(i,e,t,n,r,s,a){let o=e.has("WEBGL_multisampled_render_to_texture")?e.get("WEBGL_multisampled_render_to_texture"):null,c=typeof navigator>"u"?!1:/OculusBrowser/g.test(navigator.userAgent),l=new We,u=new WeakMap,d,h=new WeakMap,p=!1;try{p=typeof OffscreenCanvas<"u"&&new OffscreenCanvas(1,1).getContext("2d")!==null}catch{}function g(E,_){return p?new OffscreenCanvas(E,_):Gr("canvas")}function x(E,_,z){let q=1,j=Ve(E);if((j.width>z||j.height>z)&&(q=z/Math.max(j.width,j.height)),q<1)if(typeof HTMLImageElement<"u"&&E instanceof HTMLImageElement||typeof HTMLCanvasElement<"u"&&E instanceof HTMLCanvasElement||typeof ImageBitmap<"u"&&E instanceof ImageBitmap||typeof VideoFrame<"u"&&E instanceof VideoFrame){let $=Math.floor(q*j.width),Se=Math.floor(q*j.height);d===void 0&&(d=g($,Se));let re=_?g($,Se):d;return re.width=$,re.height=Se,re.getContext("2d").drawImage(E,0,0,$,Se),console.warn("THREE.WebGLRenderer: Texture has been resized from ("+j.width+"x"+j.height+") to ("+$+"x"+Se+")."),re}else return"data"in E&&console.warn("THREE.WebGLRenderer: Image in DataTexture is too big ("+j.width+"x"+j.height+")."),E;return E}function m(E){return E.generateMipmaps}function f(E){i.generateMipmap(E)}function S(E){return E.isWebGLCubeRenderTarget?i.TEXTURE_CUBE_MAP:E.isWebGL3DRenderTarget?i.TEXTURE_3D:E.isWebGLArrayRenderTarget||E.isCompressedArrayTexture?i.TEXTURE_2D_ARRAY:i.TEXTURE_2D}function M(E,_,z,q,j=!1){if(E!==null){if(i[E]!==void 0)return i[E];console.warn("THREE.WebGLRenderer: Attempt to use non-existing WebGL internal format '"+E+"'")}let $=_;if(_===i.RED&&(z===i.FLOAT&&($=i.R32F),z===i.HALF_FLOAT&&($=i.R16F),z===i.UNSIGNED_BYTE&&($=i.R8)),_===i.RED_INTEGER&&(z===i.UNSIGNED_BYTE&&($=i.R8UI),z===i.UNSIGNED_SHORT&&($=i.R16UI),z===i.UNSIGNED_INT&&($=i.R32UI),z===i.BYTE&&($=i.R8I),z===i.SHORT&&($=i.R16I),z===i.INT&&($=i.R32I)),_===i.RG&&(z===i.FLOAT&&($=i.RG32F),z===i.HALF_FLOAT&&($=i.RG16F),z===i.UNSIGNED_BYTE&&($=i.RG8)),_===i.RG_INTEGER&&(z===i.UNSIGNED_BYTE&&($=i.RG8UI),z===i.UNSIGNED_SHORT&&($=i.RG16UI),z===i.UNSIGNED_INT&&($=i.RG32UI),z===i.BYTE&&($=i.RG8I),z===i.SHORT&&($=i.RG16I),z===i.INT&&($=i.RG32I)),_===i.RGB_INTEGER&&(z===i.UNSIGNED_BYTE&&($=i.RGB8UI),z===i.UNSIGNED_SHORT&&($=i.RGB16UI),z===i.UNSIGNED_INT&&($=i.RGB32UI),z===i.BYTE&&($=i.RGB8I),z===i.SHORT&&($=i.RGB16I),z===i.INT&&($=i.RGB32I)),_===i.RGBA_INTEGER&&(z===i.UNSIGNED_BYTE&&($=i.RGBA8UI),z===i.UNSIGNED_SHORT&&($=i.RGBA16UI),z===i.UNSIGNED_INT&&($=i.RGBA32UI),z===i.BYTE&&($=i.RGBA8I),z===i.SHORT&&($=i.RGBA16I),z===i.INT&&($=i.RGBA32I)),_===i.RGB&&(z===i.UNSIGNED_INT_5_9_9_9_REV&&($=i.RGB9_E5),z===i.UNSIGNED_INT_10F_11F_11F_REV&&($=i.R11F_G11F_B10F)),_===i.RGBA){let Se=j?Hr:Ke.getTransfer(q);z===i.FLOAT&&($=i.RGBA32F),z===i.HALF_FLOAT&&($=i.RGBA16F),z===i.UNSIGNED_BYTE&&($=Se===tt?i.SRGB8_ALPHA8:i.RGBA8),z===i.UNSIGNED_SHORT_4_4_4_4&&($=i.RGBA4),z===i.UNSIGNED_SHORT_5_5_5_1&&($=i.RGB5_A1)}return($===i.R16F||$===i.R32F||$===i.RG16F||$===i.RG32F||$===i.RGBA16F||$===i.RGBA32F)&&e.get("EXT_color_buffer_float"),$}function y(E,_){let z;return E?_===null||_===pi||_===vr?z=i.DEPTH24_STENCIL8:_===Nn?z=i.DEPTH32F_STENCIL8:_===_r&&(z=i.DEPTH24_STENCIL8,console.warn("DepthTexture: 16 bit depth attachment is not supported with stencil. Using 24-bit attachment.")):_===null||_===pi||_===vr?z=i.DEPTH_COMPONENT24:_===Nn?z=i.DEPTH_COMPONENT32F:_===_r&&(z=i.DEPTH_COMPONENT16),z}function C(E,_){return m(E)===!0||E.isFramebufferTexture&&E.minFilter!==dn&&E.minFilter!==bn?Math.log2(Math.max(_.width,_.height))+1:E.mipmaps!==void 0&&E.mipmaps.length>0?E.mipmaps.length:E.isCompressedTexture&&Array.isArray(E.image)?_.mipmaps.length:1}function A(E){let _=E.target;_.removeEventListener("dispose",A),N(_),_.isVideoTexture&&u.delete(_)}function I(E){let _=E.target;_.removeEventListener("dispose",I),b(_)}function N(E){let _=n.get(E);if(_.__webglInit===void 0)return;let z=E.source,q=h.get(z);if(q){let j=q[_.__cacheKey];j.usedTimes--,j.usedTimes===0&&v(E),Object.keys(q).length===0&&h.delete(z)}n.remove(E)}function v(E){let _=n.get(E);i.deleteTexture(_.__webglTexture);let z=E.source,q=h.get(z);delete q[_.__cacheKey],a.memory.textures--}function b(E){let _=n.get(E);if(E.depthTexture&&(E.depthTexture.dispose(),n.remove(E.depthTexture)),E.isWebGLCubeRenderTarget)for(let q=0;q<6;q++){if(Array.isArray(_.__webglFramebuffer[q]))for(let j=0;j<_.__webglFramebuffer[q].length;j++)i.deleteFramebuffer(_.__webglFramebuffer[q][j]);else i.deleteFramebuffer(_.__webglFramebuffer[q]);_.__webglDepthbuffer&&i.deleteRenderbuffer(_.__webglDepthbuffer[q])}else{if(Array.isArray(_.__webglFramebuffer))for(let q=0;q<_.__webglFramebuffer.length;q++)i.deleteFramebuffer(_.__webglFramebuffer[q]);else i.deleteFramebuffer(_.__webglFramebuffer);if(_.__webglDepthbuffer&&i.deleteRenderbuffer(_.__webglDepthbuffer),_.__webglMultisampledFramebuffer&&i.deleteFramebuffer(_.__webglMultisampledFramebuffer),_.__webglColorRenderbuffer)for(let q=0;q<_.__webglColorRenderbuffer.length;q++)_.__webglColorRenderbuffer[q]&&i.deleteRenderbuffer(_.__webglColorRenderbuffer[q]);_.__webglDepthRenderbuffer&&i.deleteRenderbuffer(_.__webglDepthRenderbuffer)}let z=E.textures;for(let q=0,j=z.length;q<j;q++){let $=n.get(z[q]);$.__webglTexture&&(i.deleteTexture($.__webglTexture),a.memory.textures--),n.remove(z[q])}n.remove(E)}let T=0;function P(){T=0}function U(){let E=T;return E>=r.maxTextures&&console.warn("THREE.WebGLTextures: Trying to use "+E+" texture units while this GPU supports only "+r.maxTextures),T+=1,E}function F(E){let _=[];return _.push(E.wrapS),_.push(E.wrapT),_.push(E.wrapR||0),_.push(E.magFilter),_.push(E.minFilter),_.push(E.anisotropy),_.push(E.internalFormat),_.push(E.format),_.push(E.type),_.push(E.generateMipmaps),_.push(E.premultiplyAlpha),_.push(E.flipY),_.push(E.unpackAlignment),_.push(E.colorSpace),_.join()}function k(E,_){let z=n.get(E);if(E.isVideoTexture&&He(E),E.isRenderTargetTexture===!1&&E.isExternalTexture!==!0&&E.version>0&&z.__version!==E.version){let q=E.image;if(q===null)console.warn("THREE.WebGLRenderer: Texture marked for update but no image data found.");else if(q.complete===!1)console.warn("THREE.WebGLRenderer: Texture marked for update but image is incomplete");else{X(z,E,_);return}}else E.isExternalTexture&&(z.__webglTexture=E.sourceTexture?E.sourceTexture:null);t.bindTexture(i.TEXTURE_2D,z.__webglTexture,i.TEXTURE0+_)}function G(E,_){let z=n.get(E);if(E.isRenderTargetTexture===!1&&E.version>0&&z.__version!==E.version){X(z,E,_);return}t.bindTexture(i.TEXTURE_2D_ARRAY,z.__webglTexture,i.TEXTURE0+_)}function K(E,_){let z=n.get(E);if(E.isRenderTargetTexture===!1&&E.version>0&&z.__version!==E.version){X(z,E,_);return}t.bindTexture(i.TEXTURE_3D,z.__webglTexture,i.TEXTURE0+_)}function W(E,_){let z=n.get(E);if(E.version>0&&z.__version!==E.version){J(z,E,_);return}t.bindTexture(i.TEXTURE_CUBE_MAP,z.__webglTexture,i.TEXTURE0+_)}let se={[la]:i.REPEAT,[si]:i.CLAMP_TO_EDGE,[ca]:i.MIRRORED_REPEAT},de={[dn]:i.NEAREST,[Xd]:i.NEAREST_MIPMAP_NEAREST,[ps]:i.NEAREST_MIPMAP_LINEAR,[bn]:i.LINEAR,[Va]:i.LINEAR_MIPMAP_NEAREST,[fi]:i.LINEAR_MIPMAP_LINEAR},Ae={[Zd]:i.NEVER,[tu]:i.ALWAYS,[Jd]:i.LESS,[Gl]:i.LEQUAL,[Kd]:i.EQUAL,[eu]:i.GEQUAL,[jd]:i.GREATER,[Qd]:i.NOTEQUAL};function fe(E,_){if(_.type===Nn&&e.has("OES_texture_float_linear")===!1&&(_.magFilter===bn||_.magFilter===Va||_.magFilter===ps||_.magFilter===fi||_.minFilter===bn||_.minFilter===Va||_.minFilter===ps||_.minFilter===fi)&&console.warn("THREE.WebGLRenderer: Unable to use linear filtering with floating point textures. OES_texture_float_linear not supported on this device."),i.texParameteri(E,i.TEXTURE_WRAP_S,se[_.wrapS]),i.texParameteri(E,i.TEXTURE_WRAP_T,se[_.wrapT]),(E===i.TEXTURE_3D||E===i.TEXTURE_2D_ARRAY)&&i.texParameteri(E,i.TEXTURE_WRAP_R,se[_.wrapR]),i.texParameteri(E,i.TEXTURE_MAG_FILTER,de[_.magFilter]),i.texParameteri(E,i.TEXTURE_MIN_FILTER,de[_.minFilter]),_.compareFunction&&(i.texParameteri(E,i.TEXTURE_COMPARE_MODE,i.COMPARE_REF_TO_TEXTURE),i.texParameteri(E,i.TEXTURE_COMPARE_FUNC,Ae[_.compareFunction])),e.has("EXT_texture_filter_anisotropic")===!0){if(_.magFilter===dn||_.minFilter!==ps&&_.minFilter!==fi||_.type===Nn&&e.has("OES_texture_float_linear")===!1)return;if(_.anisotropy>1||n.get(_).__currentAnisotropy){let z=e.get("EXT_texture_filter_anisotropic");i.texParameterf(E,z.TEXTURE_MAX_ANISOTROPY_EXT,Math.min(_.anisotropy,r.getMaxAnisotropy())),n.get(_).__currentAnisotropy=_.anisotropy}}}function Oe(E,_){let z=!1;E.__webglInit===void 0&&(E.__webglInit=!0,_.addEventListener("dispose",A));let q=_.source,j=h.get(q);j===void 0&&(j={},h.set(q,j));let $=F(_);if($!==E.__cacheKey){j[$]===void 0&&(j[$]={texture:i.createTexture(),usedTimes:0},a.memory.textures++,z=!0),j[$].usedTimes++;let Se=j[E.__cacheKey];Se!==void 0&&(j[E.__cacheKey].usedTimes--,Se.usedTimes===0&&v(_)),E.__cacheKey=$,E.__webglTexture=j[$].texture}return z}function $e(E,_,z){return Math.floor(Math.floor(E/z)/_)}function Pe(E,_,z,q){let $=E.updateRanges;if($.length===0)t.texSubImage2D(i.TEXTURE_2D,0,0,0,_.width,_.height,z,q,_.data);else{$.sort((ee,ge)=>ee.start-ge.start);let Se=0;for(let ee=1;ee<$.length;ee++){let ge=$[Se],Fe=$[ee],Ie=ge.start+ge.count,he=$e(Fe.start,_.width,4),Ge=$e(ge.start,_.width,4);Fe.start<=Ie+1&&he===Ge&&$e(Fe.start+Fe.count-1,_.width,4)===he?ge.count=Math.max(ge.count,Fe.start+Fe.count-ge.start):(++Se,$[Se]=Fe)}$.length=Se+1;let re=i.getParameter(i.UNPACK_ROW_LENGTH),be=i.getParameter(i.UNPACK_SKIP_PIXELS),we=i.getParameter(i.UNPACK_SKIP_ROWS);i.pixelStorei(i.UNPACK_ROW_LENGTH,_.width);for(let ee=0,ge=$.length;ee<ge;ee++){let Fe=$[ee],Ie=Math.floor(Fe.start/4),he=Math.ceil(Fe.count/4),Ge=Ie%_.width,L=Math.floor(Ie/_.width),ie=he,oe=1;i.pixelStorei(i.UNPACK_SKIP_PIXELS,Ge),i.pixelStorei(i.UNPACK_SKIP_ROWS,L),t.texSubImage2D(i.TEXTURE_2D,0,Ge,L,ie,oe,z,q,_.data)}E.clearUpdateRanges(),i.pixelStorei(i.UNPACK_ROW_LENGTH,re),i.pixelStorei(i.UNPACK_SKIP_PIXELS,be),i.pixelStorei(i.UNPACK_SKIP_ROWS,we)}}function X(E,_,z){let q=i.TEXTURE_2D;(_.isDataArrayTexture||_.isCompressedArrayTexture)&&(q=i.TEXTURE_2D_ARRAY),_.isData3DTexture&&(q=i.TEXTURE_3D);let j=Oe(E,_),$=_.source;t.bindTexture(q,E.__webglTexture,i.TEXTURE0+z);let Se=n.get($);if($.version!==Se.__version||j===!0){t.activeTexture(i.TEXTURE0+z);let re=Ke.getPrimaries(Ke.workingColorSpace),be=_.colorSpace===Yn?null:Ke.getPrimaries(_.colorSpace),we=_.colorSpace===Yn||re===be?i.NONE:i.BROWSER_DEFAULT_WEBGL;i.pixelStorei(i.UNPACK_FLIP_Y_WEBGL,_.flipY),i.pixelStorei(i.UNPACK_PREMULTIPLY_ALPHA_WEBGL,_.premultiplyAlpha),i.pixelStorei(i.UNPACK_ALIGNMENT,_.unpackAlignment),i.pixelStorei(i.UNPACK_COLORSPACE_CONVERSION_WEBGL,we);let ee=x(_.image,!1,r.maxTextureSize);ee=Re(_,ee);let ge=s.convert(_.format,_.colorSpace),Fe=s.convert(_.type),Ie=M(_.internalFormat,ge,Fe,_.colorSpace,_.isVideoTexture);fe(q,_);let he,Ge=_.mipmaps,L=_.isVideoTexture!==!0,ie=Se.__version===void 0||j===!0,oe=$.dataReady,Me=C(_,ee);if(_.isDepthTexture)Ie=y(_.format===br,_.type),ie&&(L?t.texStorage2D(i.TEXTURE_2D,1,Ie,ee.width,ee.height):t.texImage2D(i.TEXTURE_2D,0,Ie,ee.width,ee.height,0,ge,Fe,null));else if(_.isDataTexture)if(Ge.length>0){L&&ie&&t.texStorage2D(i.TEXTURE_2D,Me,Ie,Ge[0].width,Ge[0].height);for(let te=0,Z=Ge.length;te<Z;te++)he=Ge[te],L?oe&&t.texSubImage2D(i.TEXTURE_2D,te,0,0,he.width,he.height,ge,Fe,he.data):t.texImage2D(i.TEXTURE_2D,te,Ie,he.width,he.height,0,ge,Fe,he.data);_.generateMipmaps=!1}else L?(ie&&t.texStorage2D(i.TEXTURE_2D,Me,Ie,ee.width,ee.height),oe&&Pe(_,ee,ge,Fe)):t.texImage2D(i.TEXTURE_2D,0,Ie,ee.width,ee.height,0,ge,Fe,ee.data);else if(_.isCompressedTexture)if(_.isCompressedArrayTexture){L&&ie&&t.texStorage3D(i.TEXTURE_2D_ARRAY,Me,Ie,Ge[0].width,Ge[0].height,ee.depth);for(let te=0,Z=Ge.length;te<Z;te++)if(he=Ge[te],_.format!==hn)if(ge!==null)if(L){if(oe)if(_.layerUpdates.size>0){let Te=Jl(he.width,he.height,_.format,_.type);for(let ze of _.layerUpdates){let ot=he.data.subarray(ze*Te/he.data.BYTES_PER_ELEMENT,(ze+1)*Te/he.data.BYTES_PER_ELEMENT);t.compressedTexSubImage3D(i.TEXTURE_2D_ARRAY,te,0,0,ze,he.width,he.height,1,ge,ot)}_.clearLayerUpdates()}else t.compressedTexSubImage3D(i.TEXTURE_2D_ARRAY,te,0,0,0,he.width,he.height,ee.depth,ge,he.data)}else t.compressedTexImage3D(i.TEXTURE_2D_ARRAY,te,Ie,he.width,he.height,ee.depth,0,he.data,0,0);else console.warn("THREE.WebGLRenderer: Attempt to load unsupported compressed texture format in .uploadTexture()");else L?oe&&t.texSubImage3D(i.TEXTURE_2D_ARRAY,te,0,0,0,he.width,he.height,ee.depth,ge,Fe,he.data):t.texImage3D(i.TEXTURE_2D_ARRAY,te,Ie,he.width,he.height,ee.depth,0,ge,Fe,he.data)}else{L&&ie&&t.texStorage2D(i.TEXTURE_2D,Me,Ie,Ge[0].width,Ge[0].height);for(let te=0,Z=Ge.length;te<Z;te++)he=Ge[te],_.format!==hn?ge!==null?L?oe&&t.compressedTexSubImage2D(i.TEXTURE_2D,te,0,0,he.width,he.height,ge,he.data):t.compressedTexImage2D(i.TEXTURE_2D,te,Ie,he.width,he.height,0,he.data):console.warn("THREE.WebGLRenderer: Attempt to load unsupported compressed texture format in .uploadTexture()"):L?oe&&t.texSubImage2D(i.TEXTURE_2D,te,0,0,he.width,he.height,ge,Fe,he.data):t.texImage2D(i.TEXTURE_2D,te,Ie,he.width,he.height,0,ge,Fe,he.data)}else if(_.isDataArrayTexture)if(L){if(ie&&t.texStorage3D(i.TEXTURE_2D_ARRAY,Me,Ie,ee.width,ee.height,ee.depth),oe)if(_.layerUpdates.size>0){let te=Jl(ee.width,ee.height,_.format,_.type);for(let Z of _.layerUpdates){let Te=ee.data.subarray(Z*te/ee.data.BYTES_PER_ELEMENT,(Z+1)*te/ee.data.BYTES_PER_ELEMENT);t.texSubImage3D(i.TEXTURE_2D_ARRAY,0,0,0,Z,ee.width,ee.height,1,ge,Fe,Te)}_.clearLayerUpdates()}else t.texSubImage3D(i.TEXTURE_2D_ARRAY,0,0,0,0,ee.width,ee.height,ee.depth,ge,Fe,ee.data)}else t.texImage3D(i.TEXTURE_2D_ARRAY,0,Ie,ee.width,ee.height,ee.depth,0,ge,Fe,ee.data);else if(_.isData3DTexture)L?(ie&&t.texStorage3D(i.TEXTURE_3D,Me,Ie,ee.width,ee.height,ee.depth),oe&&t.texSubImage3D(i.TEXTURE_3D,0,0,0,0,ee.width,ee.height,ee.depth,ge,Fe,ee.data)):t.texImage3D(i.TEXTURE_3D,0,Ie,ee.width,ee.height,ee.depth,0,ge,Fe,ee.data);else if(_.isFramebufferTexture){if(ie)if(L)t.texStorage2D(i.TEXTURE_2D,Me,Ie,ee.width,ee.height);else{let te=ee.width,Z=ee.height;for(let Te=0;Te<Me;Te++)t.texImage2D(i.TEXTURE_2D,Te,Ie,te,Z,0,ge,Fe,null),te>>=1,Z>>=1}}else if(Ge.length>0){if(L&&ie){let te=Ve(Ge[0]);t.texStorage2D(i.TEXTURE_2D,Me,Ie,te.width,te.height)}for(let te=0,Z=Ge.length;te<Z;te++)he=Ge[te],L?oe&&t.texSubImage2D(i.TEXTURE_2D,te,0,0,ge,Fe,he):t.texImage2D(i.TEXTURE_2D,te,Ie,ge,Fe,he);_.generateMipmaps=!1}else if(L){if(ie){let te=Ve(ee);t.texStorage2D(i.TEXTURE_2D,Me,Ie,te.width,te.height)}oe&&t.texSubImage2D(i.TEXTURE_2D,0,0,0,ge,Fe,ee)}else t.texImage2D(i.TEXTURE_2D,0,Ie,ge,Fe,ee);m(_)&&f(q),Se.__version=$.version,_.onUpdate&&_.onUpdate(_)}E.__version=_.version}function J(E,_,z){if(_.image.length!==6)return;let q=Oe(E,_),j=_.source;t.bindTexture(i.TEXTURE_CUBE_MAP,E.__webglTexture,i.TEXTURE0+z);let $=n.get(j);if(j.version!==$.__version||q===!0){t.activeTexture(i.TEXTURE0+z);let Se=Ke.getPrimaries(Ke.workingColorSpace),re=_.colorSpace===Yn?null:Ke.getPrimaries(_.colorSpace),be=_.colorSpace===Yn||Se===re?i.NONE:i.BROWSER_DEFAULT_WEBGL;i.pixelStorei(i.UNPACK_FLIP_Y_WEBGL,_.flipY),i.pixelStorei(i.UNPACK_PREMULTIPLY_ALPHA_WEBGL,_.premultiplyAlpha),i.pixelStorei(i.UNPACK_ALIGNMENT,_.unpackAlignment),i.pixelStorei(i.UNPACK_COLORSPACE_CONVERSION_WEBGL,be);let we=_.isCompressedTexture||_.image[0].isCompressedTexture,ee=_.image[0]&&_.image[0].isDataTexture,ge=[];for(let Z=0;Z<6;Z++)!we&&!ee?ge[Z]=x(_.image[Z],!0,r.maxCubemapSize):ge[Z]=ee?_.image[Z].image:_.image[Z],ge[Z]=Re(_,ge[Z]);let Fe=ge[0],Ie=s.convert(_.format,_.colorSpace),he=s.convert(_.type),Ge=M(_.internalFormat,Ie,he,_.colorSpace),L=_.isVideoTexture!==!0,ie=$.__version===void 0||q===!0,oe=j.dataReady,Me=C(_,Fe);fe(i.TEXTURE_CUBE_MAP,_);let te;if(we){L&&ie&&t.texStorage2D(i.TEXTURE_CUBE_MAP,Me,Ge,Fe.width,Fe.height);for(let Z=0;Z<6;Z++){te=ge[Z].mipmaps;for(let Te=0;Te<te.length;Te++){let ze=te[Te];_.format!==hn?Ie!==null?L?oe&&t.compressedTexSubImage2D(i.TEXTURE_CUBE_MAP_POSITIVE_X+Z,Te,0,0,ze.width,ze.height,Ie,ze.data):t.compressedTexImage2D(i.TEXTURE_CUBE_MAP_POSITIVE_X+Z,Te,Ge,ze.width,ze.height,0,ze.data):console.warn("THREE.WebGLRenderer: Attempt to load unsupported compressed texture format in .setTextureCube()"):L?oe&&t.texSubImage2D(i.TEXTURE_CUBE_MAP_POSITIVE_X+Z,Te,0,0,ze.width,ze.height,Ie,he,ze.data):t.texImage2D(i.TEXTURE_CUBE_MAP_POSITIVE_X+Z,Te,Ge,ze.width,ze.height,0,Ie,he,ze.data)}}}else{if(te=_.mipmaps,L&&ie){te.length>0&&Me++;let Z=Ve(ge[0]);t.texStorage2D(i.TEXTURE_CUBE_MAP,Me,Ge,Z.width,Z.height)}for(let Z=0;Z<6;Z++)if(ee){L?oe&&t.texSubImage2D(i.TEXTURE_CUBE_MAP_POSITIVE_X+Z,0,0,0,ge[Z].width,ge[Z].height,Ie,he,ge[Z].data):t.texImage2D(i.TEXTURE_CUBE_MAP_POSITIVE_X+Z,0,Ge,ge[Z].width,ge[Z].height,0,Ie,he,ge[Z].data);for(let Te=0;Te<te.length;Te++){let ot=te[Te].image[Z].image;L?oe&&t.texSubImage2D(i.TEXTURE_CUBE_MAP_POSITIVE_X+Z,Te+1,0,0,ot.width,ot.height,Ie,he,ot.data):t.texImage2D(i.TEXTURE_CUBE_MAP_POSITIVE_X+Z,Te+1,Ge,ot.width,ot.height,0,Ie,he,ot.data)}}else{L?oe&&t.texSubImage2D(i.TEXTURE_CUBE_MAP_POSITIVE_X+Z,0,0,0,Ie,he,ge[Z]):t.texImage2D(i.TEXTURE_CUBE_MAP_POSITIVE_X+Z,0,Ge,Ie,he,ge[Z]);for(let Te=0;Te<te.length;Te++){let ze=te[Te];L?oe&&t.texSubImage2D(i.TEXTURE_CUBE_MAP_POSITIVE_X+Z,Te+1,0,0,Ie,he,ze.image[Z]):t.texImage2D(i.TEXTURE_CUBE_MAP_POSITIVE_X+Z,Te+1,Ge,Ie,he,ze.image[Z])}}}m(_)&&f(i.TEXTURE_CUBE_MAP),$.__version=j.version,_.onUpdate&&_.onUpdate(_)}E.__version=_.version}function Y(E,_,z,q,j,$){let Se=s.convert(z.format,z.colorSpace),re=s.convert(z.type),be=M(z.internalFormat,Se,re,z.colorSpace),we=n.get(_),ee=n.get(z);if(ee.__renderTarget=_,!we.__hasExternalTextures){let ge=Math.max(1,_.width>>$),Fe=Math.max(1,_.height>>$);j===i.TEXTURE_3D||j===i.TEXTURE_2D_ARRAY?t.texImage3D(j,$,be,ge,Fe,_.depth,0,Se,re,null):t.texImage2D(j,$,be,ge,Fe,0,Se,re,null)}t.bindFramebuffer(i.FRAMEBUFFER,E),_e(_)?o.framebufferTexture2DMultisampleEXT(i.FRAMEBUFFER,q,j,ee.__webglTexture,0,Je(_)):(j===i.TEXTURE_2D||j>=i.TEXTURE_CUBE_MAP_POSITIVE_X&&j<=i.TEXTURE_CUBE_MAP_NEGATIVE_Z)&&i.framebufferTexture2D(i.FRAMEBUFFER,q,j,ee.__webglTexture,$),t.bindFramebuffer(i.FRAMEBUFFER,null)}function ae(E,_,z){if(i.bindRenderbuffer(i.RENDERBUFFER,E),_.depthBuffer){let q=_.depthTexture,j=q&&q.isDepthTexture?q.type:null,$=y(_.stencilBuffer,j),Se=_.stencilBuffer?i.DEPTH_STENCIL_ATTACHMENT:i.DEPTH_ATTACHMENT,re=Je(_);_e(_)?o.renderbufferStorageMultisampleEXT(i.RENDERBUFFER,re,$,_.width,_.height):z?i.renderbufferStorageMultisample(i.RENDERBUFFER,re,$,_.width,_.height):i.renderbufferStorage(i.RENDERBUFFER,$,_.width,_.height),i.framebufferRenderbuffer(i.FRAMEBUFFER,Se,i.RENDERBUFFER,E)}else{let q=_.textures;for(let j=0;j<q.length;j++){let $=q[j],Se=s.convert($.format,$.colorSpace),re=s.convert($.type),be=M($.internalFormat,Se,re,$.colorSpace),we=Je(_);z&&_e(_)===!1?i.renderbufferStorageMultisample(i.RENDERBUFFER,we,be,_.width,_.height):_e(_)?o.renderbufferStorageMultisampleEXT(i.RENDERBUFFER,we,be,_.width,_.height):i.renderbufferStorage(i.RENDERBUFFER,be,_.width,_.height)}}i.bindRenderbuffer(i.RENDERBUFFER,null)}function pe(E,_){if(_&&_.isWebGLCubeRenderTarget)throw new Error("Depth Texture with cube render targets is not supported");if(t.bindFramebuffer(i.FRAMEBUFFER,E),!(_.depthTexture&&_.depthTexture.isDepthTexture))throw new Error("renderTarget.depthTexture must be an instance of THREE.DepthTexture");let q=n.get(_.depthTexture);q.__renderTarget=_,(!q.__webglTexture||_.depthTexture.image.width!==_.width||_.depthTexture.image.height!==_.height)&&(_.depthTexture.image.width=_.width,_.depthTexture.image.height=_.height,_.depthTexture.needsUpdate=!0),k(_.depthTexture,0);let j=q.__webglTexture,$=Je(_);if(_.depthTexture.format===cr)_e(_)?o.framebufferTexture2DMultisampleEXT(i.FRAMEBUFFER,i.DEPTH_ATTACHMENT,i.TEXTURE_2D,j,0,$):i.framebufferTexture2D(i.FRAMEBUFFER,i.DEPTH_ATTACHMENT,i.TEXTURE_2D,j,0);else if(_.depthTexture.format===br)_e(_)?o.framebufferTexture2DMultisampleEXT(i.FRAMEBUFFER,i.DEPTH_STENCIL_ATTACHMENT,i.TEXTURE_2D,j,0,$):i.framebufferTexture2D(i.FRAMEBUFFER,i.DEPTH_STENCIL_ATTACHMENT,i.TEXTURE_2D,j,0);else throw new Error("Unknown depthTexture format")}function Ce(E){let _=n.get(E),z=E.isWebGLCubeRenderTarget===!0;if(_.__boundDepthTexture!==E.depthTexture){let q=E.depthTexture;if(_.__depthDisposeCallback&&_.__depthDisposeCallback(),q){let j=()=>{delete _.__boundDepthTexture,delete _.__depthDisposeCallback,q.removeEventListener("dispose",j)};q.addEventListener("dispose",j),_.__depthDisposeCallback=j}_.__boundDepthTexture=q}if(E.depthTexture&&!_.__autoAllocateDepthBuffer){if(z)throw new Error("target.depthTexture not supported in Cube render targets");let q=E.texture.mipmaps;q&&q.length>0?pe(_.__webglFramebuffer[0],E):pe(_.__webglFramebuffer,E)}else if(z){_.__webglDepthbuffer=[];for(let q=0;q<6;q++)if(t.bindFramebuffer(i.FRAMEBUFFER,_.__webglFramebuffer[q]),_.__webglDepthbuffer[q]===void 0)_.__webglDepthbuffer[q]=i.createRenderbuffer(),ae(_.__webglDepthbuffer[q],E,!1);else{let j=E.stencilBuffer?i.DEPTH_STENCIL_ATTACHMENT:i.DEPTH_ATTACHMENT,$=_.__webglDepthbuffer[q];i.bindRenderbuffer(i.RENDERBUFFER,$),i.framebufferRenderbuffer(i.FRAMEBUFFER,j,i.RENDERBUFFER,$)}}else{let q=E.texture.mipmaps;if(q&&q.length>0?t.bindFramebuffer(i.FRAMEBUFFER,_.__webglFramebuffer[0]):t.bindFramebuffer(i.FRAMEBUFFER,_.__webglFramebuffer),_.__webglDepthbuffer===void 0)_.__webglDepthbuffer=i.createRenderbuffer(),ae(_.__webglDepthbuffer,E,!1);else{let j=E.stencilBuffer?i.DEPTH_STENCIL_ATTACHMENT:i.DEPTH_ATTACHMENT,$=_.__webglDepthbuffer;i.bindRenderbuffer(i.RENDERBUFFER,$),i.framebufferRenderbuffer(i.FRAMEBUFFER,j,i.RENDERBUFFER,$)}}t.bindFramebuffer(i.FRAMEBUFFER,null)}function it(E,_,z){let q=n.get(E);_!==void 0&&Y(q.__webglFramebuffer,E,E.texture,i.COLOR_ATTACHMENT0,i.TEXTURE_2D,0),z!==void 0&&Ce(E)}function R(E){let _=E.texture,z=n.get(E),q=n.get(_);E.addEventListener("dispose",I);let j=E.textures,$=E.isWebGLCubeRenderTarget===!0,Se=j.length>1;if(Se||(q.__webglTexture===void 0&&(q.__webglTexture=i.createTexture()),q.__version=_.version,a.memory.textures++),$){z.__webglFramebuffer=[];for(let re=0;re<6;re++)if(_.mipmaps&&_.mipmaps.length>0){z.__webglFramebuffer[re]=[];for(let be=0;be<_.mipmaps.length;be++)z.__webglFramebuffer[re][be]=i.createFramebuffer()}else z.__webglFramebuffer[re]=i.createFramebuffer()}else{if(_.mipmaps&&_.mipmaps.length>0){z.__webglFramebuffer=[];for(let re=0;re<_.mipmaps.length;re++)z.__webglFramebuffer[re]=i.createFramebuffer()}else z.__webglFramebuffer=i.createFramebuffer();if(Se)for(let re=0,be=j.length;re<be;re++){let we=n.get(j[re]);we.__webglTexture===void 0&&(we.__webglTexture=i.createTexture(),a.memory.textures++)}if(E.samples>0&&_e(E)===!1){z.__webglMultisampledFramebuffer=i.createFramebuffer(),z.__webglColorRenderbuffer=[],t.bindFramebuffer(i.FRAMEBUFFER,z.__webglMultisampledFramebuffer);for(let re=0;re<j.length;re++){let be=j[re];z.__webglColorRenderbuffer[re]=i.createRenderbuffer(),i.bindRenderbuffer(i.RENDERBUFFER,z.__webglColorRenderbuffer[re]);let we=s.convert(be.format,be.colorSpace),ee=s.convert(be.type),ge=M(be.internalFormat,we,ee,be.colorSpace,E.isXRRenderTarget===!0),Fe=Je(E);i.renderbufferStorageMultisample(i.RENDERBUFFER,Fe,ge,E.width,E.height),i.framebufferRenderbuffer(i.FRAMEBUFFER,i.COLOR_ATTACHMENT0+re,i.RENDERBUFFER,z.__webglColorRenderbuffer[re])}i.bindRenderbuffer(i.RENDERBUFFER,null),E.depthBuffer&&(z.__webglDepthRenderbuffer=i.createRenderbuffer(),ae(z.__webglDepthRenderbuffer,E,!0)),t.bindFramebuffer(i.FRAMEBUFFER,null)}}if($){t.bindTexture(i.TEXTURE_CUBE_MAP,q.__webglTexture),fe(i.TEXTURE_CUBE_MAP,_);for(let re=0;re<6;re++)if(_.mipmaps&&_.mipmaps.length>0)for(let be=0;be<_.mipmaps.length;be++)Y(z.__webglFramebuffer[re][be],E,_,i.COLOR_ATTACHMENT0,i.TEXTURE_CUBE_MAP_POSITIVE_X+re,be);else Y(z.__webglFramebuffer[re],E,_,i.COLOR_ATTACHMENT0,i.TEXTURE_CUBE_MAP_POSITIVE_X+re,0);m(_)&&f(i.TEXTURE_CUBE_MAP),t.unbindTexture()}else if(Se){for(let re=0,be=j.length;re<be;re++){let we=j[re],ee=n.get(we),ge=i.TEXTURE_2D;(E.isWebGL3DRenderTarget||E.isWebGLArrayRenderTarget)&&(ge=E.isWebGL3DRenderTarget?i.TEXTURE_3D:i.TEXTURE_2D_ARRAY),t.bindTexture(ge,ee.__webglTexture),fe(ge,we),Y(z.__webglFramebuffer,E,we,i.COLOR_ATTACHMENT0+re,ge,0),m(we)&&f(ge)}t.unbindTexture()}else{let re=i.TEXTURE_2D;if((E.isWebGL3DRenderTarget||E.isWebGLArrayRenderTarget)&&(re=E.isWebGL3DRenderTarget?i.TEXTURE_3D:i.TEXTURE_2D_ARRAY),t.bindTexture(re,q.__webglTexture),fe(re,_),_.mipmaps&&_.mipmaps.length>0)for(let be=0;be<_.mipmaps.length;be++)Y(z.__webglFramebuffer[be],E,_,i.COLOR_ATTACHMENT0,re,be);else Y(z.__webglFramebuffer,E,_,i.COLOR_ATTACHMENT0,re,0);m(_)&&f(re),t.unbindTexture()}E.depthBuffer&&Ce(E)}function qe(E){let _=E.textures;for(let z=0,q=_.length;z<q;z++){let j=_[z];if(m(j)){let $=S(E),Se=n.get(j).__webglTexture;t.bindTexture($,Se),f($),t.unbindTexture()}}}let ue=[],ye=[];function le(E){if(E.samples>0){if(_e(E)===!1){let _=E.textures,z=E.width,q=E.height,j=i.COLOR_BUFFER_BIT,$=E.stencilBuffer?i.DEPTH_STENCIL_ATTACHMENT:i.DEPTH_ATTACHMENT,Se=n.get(E),re=_.length>1;if(re)for(let we=0;we<_.length;we++)t.bindFramebuffer(i.FRAMEBUFFER,Se.__webglMultisampledFramebuffer),i.framebufferRenderbuffer(i.FRAMEBUFFER,i.COLOR_ATTACHMENT0+we,i.RENDERBUFFER,null),t.bindFramebuffer(i.FRAMEBUFFER,Se.__webglFramebuffer),i.framebufferTexture2D(i.DRAW_FRAMEBUFFER,i.COLOR_ATTACHMENT0+we,i.TEXTURE_2D,null,0);t.bindFramebuffer(i.READ_FRAMEBUFFER,Se.__webglMultisampledFramebuffer);let be=E.texture.mipmaps;be&&be.length>0?t.bindFramebuffer(i.DRAW_FRAMEBUFFER,Se.__webglFramebuffer[0]):t.bindFramebuffer(i.DRAW_FRAMEBUFFER,Se.__webglFramebuffer);for(let we=0;we<_.length;we++){if(E.resolveDepthBuffer&&(E.depthBuffer&&(j|=i.DEPTH_BUFFER_BIT),E.stencilBuffer&&E.resolveStencilBuffer&&(j|=i.STENCIL_BUFFER_BIT)),re){i.framebufferRenderbuffer(i.READ_FRAMEBUFFER,i.COLOR_ATTACHMENT0,i.RENDERBUFFER,Se.__webglColorRenderbuffer[we]);let ee=n.get(_[we]).__webglTexture;i.framebufferTexture2D(i.DRAW_FRAMEBUFFER,i.COLOR_ATTACHMENT0,i.TEXTURE_2D,ee,0)}i.blitFramebuffer(0,0,z,q,0,0,z,q,j,i.NEAREST),c===!0&&(ue.length=0,ye.length=0,ue.push(i.COLOR_ATTACHMENT0+we),E.depthBuffer&&E.resolveDepthBuffer===!1&&(ue.push($),ye.push($),i.invalidateFramebuffer(i.DRAW_FRAMEBUFFER,ye)),i.invalidateFramebuffer(i.READ_FRAMEBUFFER,ue))}if(t.bindFramebuffer(i.READ_FRAMEBUFFER,null),t.bindFramebuffer(i.DRAW_FRAMEBUFFER,null),re)for(let we=0;we<_.length;we++){t.bindFramebuffer(i.FRAMEBUFFER,Se.__webglMultisampledFramebuffer),i.framebufferRenderbuffer(i.FRAMEBUFFER,i.COLOR_ATTACHMENT0+we,i.RENDERBUFFER,Se.__webglColorRenderbuffer[we]);let ee=n.get(_[we]).__webglTexture;t.bindFramebuffer(i.FRAMEBUFFER,Se.__webglFramebuffer),i.framebufferTexture2D(i.DRAW_FRAMEBUFFER,i.COLOR_ATTACHMENT0+we,i.TEXTURE_2D,ee,0)}t.bindFramebuffer(i.DRAW_FRAMEBUFFER,Se.__webglMultisampledFramebuffer)}else if(E.depthBuffer&&E.resolveDepthBuffer===!1&&c){let _=E.stencilBuffer?i.DEPTH_STENCIL_ATTACHMENT:i.DEPTH_ATTACHMENT;i.invalidateFramebuffer(i.DRAW_FRAMEBUFFER,[_])}}}function Je(E){return Math.min(r.maxSamples,E.samples)}function _e(E){let _=n.get(E);return E.samples>0&&e.has("WEBGL_multisampled_render_to_texture")===!0&&_.__useRenderToTexture!==!1}function He(E){let _=a.render.frame;u.get(E)!==_&&(u.set(E,_),E.update())}function Re(E,_){let z=E.colorSpace,q=E.format,j=E.type;return E.isCompressedTexture===!0||E.isVideoTexture===!0||z!==Ti&&z!==Yn&&(Ke.getTransfer(z)===tt?(q!==hn||j!==Sn)&&console.warn("THREE.WebGLTextures: sRGB encoded textures have to use RGBAFormat and UnsignedByteType."):console.error("THREE.WebGLTextures: Unsupported texture color space:",z)),_}function Ve(E){return typeof HTMLImageElement<"u"&&E instanceof HTMLImageElement?(l.width=E.naturalWidth||E.width,l.height=E.naturalHeight||E.height):typeof VideoFrame<"u"&&E instanceof VideoFrame?(l.width=E.displayWidth,l.height=E.displayHeight):(l.width=E.width,l.height=E.height),l}this.allocateTextureUnit=U,this.resetTextureUnits=P,this.setTexture2D=k,this.setTexture2DArray=G,this.setTexture3D=K,this.setTextureCube=W,this.rebindTextures=it,this.setupRenderTarget=R,this.updateRenderTargetMipmap=qe,this.updateMultisampleRenderTarget=le,this.setupDepthRenderbuffer=Ce,this.setupFrameBufferTexture=Y,this.useMultisampledRTT=_e}function $0(i,e){function t(n,r=Yn){let s,a=Ke.getTransfer(r);if(n===Sn)return i.UNSIGNED_BYTE;if(n===Wa)return i.UNSIGNED_SHORT_4_4_4_4;if(n===Xa)return i.UNSIGNED_SHORT_5_5_5_1;if(n===Ul)return i.UNSIGNED_INT_5_9_9_9_REV;if(n===Ol)return i.UNSIGNED_INT_10F_11F_11F_REV;if(n===Ll)return i.BYTE;if(n===Fl)return i.SHORT;if(n===_r)return i.UNSIGNED_SHORT;if(n===Ga)return i.INT;if(n===pi)return i.UNSIGNED_INT;if(n===Nn)return i.FLOAT;if(n===yr)return i.HALF_FLOAT;if(n===Bl)return i.ALPHA;if(n===zl)return i.RGB;if(n===hn)return i.RGBA;if(n===cr)return i.DEPTH_COMPONENT;if(n===br)return i.DEPTH_STENCIL;if(n===kl)return i.RED;if(n===$a)return i.RED_INTEGER;if(n===Hl)return i.RG;if(n===qa)return i.RG_INTEGER;if(n===Ya)return i.RGBA_INTEGER;if(n===ms||n===gs||n===xs||n===_s)if(a===tt)if(s=e.get("WEBGL_compressed_texture_s3tc_srgb"),s!==null){if(n===ms)return s.COMPRESSED_SRGB_S3TC_DXT1_EXT;if(n===gs)return s.COMPRESSED_SRGB_ALPHA_S3TC_DXT1_EXT;if(n===xs)return s.COMPRESSED_SRGB_ALPHA_S3TC_DXT3_EXT;if(n===_s)return s.COMPRESSED_SRGB_ALPHA_S3TC_DXT5_EXT}else return null;else if(s=e.get("WEBGL_compressed_texture_s3tc"),s!==null){if(n===ms)return s.COMPRESSED_RGB_S3TC_DXT1_EXT;if(n===gs)return s.COMPRESSED_RGBA_S3TC_DXT1_EXT;if(n===xs)return s.COMPRESSED_RGBA_S3TC_DXT3_EXT;if(n===_s)return s.COMPRESSED_RGBA_S3TC_DXT5_EXT}else return null;if(n===Za||n===Ja||n===Ka||n===ja)if(s=e.get("WEBGL_compressed_texture_pvrtc"),s!==null){if(n===Za)return s.COMPRESSED_RGB_PVRTC_4BPPV1_IMG;if(n===Ja)return s.COMPRESSED_RGB_PVRTC_2BPPV1_IMG;if(n===Ka)return s.COMPRESSED_RGBA_PVRTC_4BPPV1_IMG;if(n===ja)return s.COMPRESSED_RGBA_PVRTC_2BPPV1_IMG}else return null;if(n===Qa||n===eo||n===to)if(s=e.get("WEBGL_compressed_texture_etc"),s!==null){if(n===Qa||n===eo)return a===tt?s.COMPRESSED_SRGB8_ETC2:s.COMPRESSED_RGB8_ETC2;if(n===to)return a===tt?s.COMPRESSED_SRGB8_ALPHA8_ETC2_EAC:s.COMPRESSED_RGBA8_ETC2_EAC}else return null;if(n===no||n===io||n===ro||n===so||n===ao||n===oo||n===lo||n===co||n===uo||n===ho||n===fo||n===po||n===mo||n===go)if(s=e.get("WEBGL_compressed_texture_astc"),s!==null){if(n===no)return a===tt?s.COMPRESSED_SRGB8_ALPHA8_ASTC_4x4_KHR:s.COMPRESSED_RGBA_ASTC_4x4_KHR;if(n===io)return a===tt?s.COMPRESSED_SRGB8_ALPHA8_ASTC_5x4_KHR:s.COMPRESSED_RGBA_ASTC_5x4_KHR;if(n===ro)return a===tt?s.COMPRESSED_SRGB8_ALPHA8_ASTC_5x5_KHR:s.COMPRESSED_RGBA_ASTC_5x5_KHR;if(n===so)return a===tt?s.COMPRESSED_SRGB8_ALPHA8_ASTC_6x5_KHR:s.COMPRESSED_RGBA_ASTC_6x5_KHR;if(n===ao)return a===tt?s.COMPRESSED_SRGB8_ALPHA8_ASTC_6x6_KHR:s.COMPRESSED_RGBA_ASTC_6x6_KHR;if(n===oo)return a===tt?s.COMPRESSED_SRGB8_ALPHA8_ASTC_8x5_KHR:s.COMPRESSED_RGBA_ASTC_8x5_KHR;if(n===lo)return a===tt?s.COMPRESSED_SRGB8_ALPHA8_ASTC_8x6_KHR:s.COMPRESSED_RGBA_ASTC_8x6_KHR;if(n===co)return a===tt?s.COMPRESSED_SRGB8_ALPHA8_ASTC_8x8_KHR:s.COMPRESSED_RGBA_ASTC_8x8_KHR;if(n===uo)return a===tt?s.COMPRESSED_SRGB8_ALPHA8_ASTC_10x5_KHR:s.COMPRESSED_RGBA_ASTC_10x5_KHR;if(n===ho)return a===tt?s.COMPRESSED_SRGB8_ALPHA8_ASTC_10x6_KHR:s.COMPRESSED_RGBA_ASTC_10x6_KHR;if(n===fo)return a===tt?s.COMPRESSED_SRGB8_ALPHA8_ASTC_10x8_KHR:s.COMPRESSED_RGBA_ASTC_10x8_KHR;if(n===po)return a===tt?s.COMPRESSED_SRGB8_ALPHA8_ASTC_10x10_KHR:s.COMPRESSED_RGBA_ASTC_10x10_KHR;if(n===mo)return a===tt?s.COMPRESSED_SRGB8_ALPHA8_ASTC_12x10_KHR:s.COMPRESSED_RGBA_ASTC_12x10_KHR;if(n===go)return a===tt?s.COMPRESSED_SRGB8_ALPHA8_ASTC_12x12_KHR:s.COMPRESSED_RGBA_ASTC_12x12_KHR}else return null;if(n===xo||n===_o||n===yo)if(s=e.get("EXT_texture_compression_bptc"),s!==null){if(n===xo)return a===tt?s.COMPRESSED_SRGB_ALPHA_BPTC_UNORM_EXT:s.COMPRESSED_RGBA_BPTC_UNORM_EXT;if(n===_o)return s.COMPRESSED_RGB_BPTC_SIGNED_FLOAT_EXT;if(n===yo)return s.COMPRESSED_RGB_BPTC_UNSIGNED_FLOAT_EXT}else return null;if(n===vo||n===bo||n===wo||n===Mo)if(s=e.get("EXT_texture_compression_rgtc"),s!==null){if(n===vo)return s.COMPRESSED_RED_RGTC1_EXT;if(n===bo)return s.COMPRESSED_SIGNED_RED_RGTC1_EXT;if(n===wo)return s.COMPRESSED_RED_GREEN_RGTC2_EXT;if(n===Mo)return s.COMPRESSED_SIGNED_RED_GREEN_RGTC2_EXT}else return null;return n===vr?i.UNSIGNED_INT_24_8:i[n]!==void 0?i[n]:null}return{convert:t}}var q0=`
void main() {

	gl_Position = vec4( position, 1.0 );

}`,Y0=`
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

}`,cc=class{constructor(){this.texture=null,this.mesh=null,this.depthNear=0,this.depthFar=0}init(e,t){if(this.texture===null){let n=new ns(e.texture);(e.depthNear!==t.depthNear||e.depthFar!==t.depthFar)&&(this.depthNear=e.depthNear,this.depthFar=e.depthFar),this.texture=n}}getMesh(e){if(this.texture!==null&&this.mesh===null){let t=e.cameras[0].viewport,n=new tn({vertexShader:q0,fragmentShader:Y0,uniforms:{depthColor:{value:this.texture},depthWidth:{value:t.z},depthHeight:{value:t.w}}});this.mesh=new dt(new Ai(20,20),n)}return this.mesh}reset(){this.texture=null,this.mesh=null}getDepthTexture(){return this.texture}},dc=class extends Wn{constructor(e,t){super();let n=this,r=null,s=1,a=null,o="local-floor",c=1,l=null,u=null,d=null,h=null,p=null,g=null,x=typeof XRWebGLBinding<"u",m=new cc,f={},S=t.getContextAttributes(),M=null,y=null,C=[],A=[],I=new We,N=null,v=new Dt;v.viewport=new xt;let b=new Dt;b.viewport=new xt;let T=[v,b],P=new Na,U=null,F=null;this.cameraAutoUpdate=!0,this.enabled=!1,this.isPresenting=!1,this.getController=function(X){let J=C[X];return J===void 0&&(J=new pr,C[X]=J),J.getTargetRaySpace()},this.getControllerGrip=function(X){let J=C[X];return J===void 0&&(J=new pr,C[X]=J),J.getGripSpace()},this.getHand=function(X){let J=C[X];return J===void 0&&(J=new pr,C[X]=J),J.getHandSpace()};function k(X){let J=A.indexOf(X.inputSource);if(J===-1)return;let Y=C[J];Y!==void 0&&(Y.update(X.inputSource,X.frame,l||a),Y.dispatchEvent({type:X.type,data:X.inputSource}))}function G(){r.removeEventListener("select",k),r.removeEventListener("selectstart",k),r.removeEventListener("selectend",k),r.removeEventListener("squeeze",k),r.removeEventListener("squeezestart",k),r.removeEventListener("squeezeend",k),r.removeEventListener("end",G),r.removeEventListener("inputsourceschange",K);for(let X=0;X<C.length;X++){let J=A[X];J!==null&&(A[X]=null,C[X].disconnect(J))}U=null,F=null,m.reset();for(let X in f)delete f[X];e.setRenderTarget(M),p=null,h=null,d=null,r=null,y=null,Pe.stop(),n.isPresenting=!1,e.setPixelRatio(N),e.setSize(I.width,I.height,!1),n.dispatchEvent({type:"sessionend"})}this.setFramebufferScaleFactor=function(X){s=X,n.isPresenting===!0&&console.warn("THREE.WebXRManager: Cannot change framebuffer scale while presenting.")},this.setReferenceSpaceType=function(X){o=X,n.isPresenting===!0&&console.warn("THREE.WebXRManager: Cannot change reference space type while presenting.")},this.getReferenceSpace=function(){return l||a},this.setReferenceSpace=function(X){l=X},this.getBaseLayer=function(){return h!==null?h:p},this.getBinding=function(){return d===null&&x&&(d=new XRWebGLBinding(r,t)),d},this.getFrame=function(){return g},this.getSession=function(){return r},this.setSession=async function(X){if(r=X,r!==null){if(M=e.getRenderTarget(),r.addEventListener("select",k),r.addEventListener("selectstart",k),r.addEventListener("selectend",k),r.addEventListener("squeeze",k),r.addEventListener("squeezestart",k),r.addEventListener("squeezeend",k),r.addEventListener("end",G),r.addEventListener("inputsourceschange",K),S.xrCompatible!==!0&&await t.makeXRCompatible(),N=e.getPixelRatio(),e.getSize(I),x&&"createProjectionLayer"in XRWebGLBinding.prototype){let Y=null,ae=null,pe=null;S.depth&&(pe=S.stencil?t.DEPTH24_STENCIL8:t.DEPTH_COMPONENT24,Y=S.stencil?br:cr,ae=S.stencil?vr:pi);let Ce={colorFormat:t.RGBA8,depthFormat:pe,scaleFactor:s};d=this.getBinding(),h=d.createProjectionLayer(Ce),r.updateRenderState({layers:[h]}),e.setPixelRatio(1),e.setSize(h.textureWidth,h.textureHeight,!1),y=new Rn(h.textureWidth,h.textureHeight,{format:hn,type:Sn,depthTexture:new ts(h.textureWidth,h.textureHeight,ae,void 0,void 0,void 0,void 0,void 0,void 0,Y),stencilBuffer:S.stencil,colorSpace:e.outputColorSpace,samples:S.antialias?4:0,resolveDepthBuffer:h.ignoreDepthValues===!1,resolveStencilBuffer:h.ignoreDepthValues===!1})}else{let Y={antialias:S.antialias,alpha:!0,depth:S.depth,stencil:S.stencil,framebufferScaleFactor:s};p=new XRWebGLLayer(r,t,Y),r.updateRenderState({baseLayer:p}),e.setPixelRatio(1),e.setSize(p.framebufferWidth,p.framebufferHeight,!1),y=new Rn(p.framebufferWidth,p.framebufferHeight,{format:hn,type:Sn,colorSpace:e.outputColorSpace,stencilBuffer:S.stencil,resolveDepthBuffer:p.ignoreDepthValues===!1,resolveStencilBuffer:p.ignoreDepthValues===!1})}y.isXRRenderTarget=!0,this.setFoveation(c),l=null,a=await r.requestReferenceSpace(o),Pe.setContext(r),Pe.start(),n.isPresenting=!0,n.dispatchEvent({type:"sessionstart"})}},this.getEnvironmentBlendMode=function(){if(r!==null)return r.environmentBlendMode},this.getDepthTexture=function(){return m.getDepthTexture()};function K(X){for(let J=0;J<X.removed.length;J++){let Y=X.removed[J],ae=A.indexOf(Y);ae>=0&&(A[ae]=null,C[ae].disconnect(Y))}for(let J=0;J<X.added.length;J++){let Y=X.added[J],ae=A.indexOf(Y);if(ae===-1){for(let Ce=0;Ce<C.length;Ce++)if(Ce>=A.length){A.push(Y),ae=Ce;break}else if(A[Ce]===null){A[Ce]=Y,ae=Ce;break}if(ae===-1)break}let pe=C[ae];pe&&pe.connect(Y)}}let W=new D,se=new D;function de(X,J,Y){W.setFromMatrixPosition(J.matrixWorld),se.setFromMatrixPosition(Y.matrixWorld);let ae=W.distanceTo(se),pe=J.projectionMatrix.elements,Ce=Y.projectionMatrix.elements,it=pe[14]/(pe[10]-1),R=pe[14]/(pe[10]+1),qe=(pe[9]+1)/pe[5],ue=(pe[9]-1)/pe[5],ye=(pe[8]-1)/pe[0],le=(Ce[8]+1)/Ce[0],Je=it*ye,_e=it*le,He=ae/(-ye+le),Re=He*-ye;if(J.matrixWorld.decompose(X.position,X.quaternion,X.scale),X.translateX(Re),X.translateZ(He),X.matrixWorld.compose(X.position,X.quaternion,X.scale),X.matrixWorldInverse.copy(X.matrixWorld).invert(),pe[10]===-1)X.projectionMatrix.copy(J.projectionMatrix),X.projectionMatrixInverse.copy(J.projectionMatrixInverse);else{let Ve=it+He,E=R+He,_=Je-Re,z=_e+(ae-Re),q=qe*R/E*Ve,j=ue*R/E*Ve;X.projectionMatrix.makePerspective(_,z,q,j,Ve,E),X.projectionMatrixInverse.copy(X.projectionMatrix).invert()}}function Ae(X,J){J===null?X.matrixWorld.copy(X.matrix):X.matrixWorld.multiplyMatrices(J.matrixWorld,X.matrix),X.matrixWorldInverse.copy(X.matrixWorld).invert()}this.updateCamera=function(X){if(r===null)return;let J=X.near,Y=X.far;m.texture!==null&&(m.depthNear>0&&(J=m.depthNear),m.depthFar>0&&(Y=m.depthFar)),P.near=b.near=v.near=J,P.far=b.far=v.far=Y,(U!==P.near||F!==P.far)&&(r.updateRenderState({depthNear:P.near,depthFar:P.far}),U=P.near,F=P.far),P.layers.mask=X.layers.mask|6,v.layers.mask=P.layers.mask&3,b.layers.mask=P.layers.mask&5;let ae=X.parent,pe=P.cameras;Ae(P,ae);for(let Ce=0;Ce<pe.length;Ce++)Ae(pe[Ce],ae);pe.length===2?de(P,v,b):P.projectionMatrix.copy(v.projectionMatrix),fe(X,P,ae)};function fe(X,J,Y){Y===null?X.matrix.copy(J.matrixWorld):(X.matrix.copy(Y.matrixWorld),X.matrix.invert(),X.matrix.multiply(J.matrixWorld)),X.matrix.decompose(X.position,X.quaternion,X.scale),X.updateMatrixWorld(!0),X.projectionMatrix.copy(J.projectionMatrix),X.projectionMatrixInverse.copy(J.projectionMatrixInverse),X.isPerspectiveCamera&&(X.fov=dr*2*Math.atan(1/X.projectionMatrix.elements[5]),X.zoom=1)}this.getCamera=function(){return P},this.getFoveation=function(){if(!(h===null&&p===null))return c},this.setFoveation=function(X){c=X,h!==null&&(h.fixedFoveation=X),p!==null&&p.fixedFoveation!==void 0&&(p.fixedFoveation=X)},this.hasDepthSensing=function(){return m.texture!==null},this.getDepthSensingMesh=function(){return m.getMesh(P)},this.getCameraTexture=function(X){return f[X]};let Oe=null;function $e(X,J){if(u=J.getViewerPose(l||a),g=J,u!==null){let Y=u.views;p!==null&&(e.setRenderTargetFramebuffer(y,p.framebuffer),e.setRenderTarget(y));let ae=!1;Y.length!==P.cameras.length&&(P.cameras.length=0,ae=!0);for(let R=0;R<Y.length;R++){let qe=Y[R],ue=null;if(p!==null)ue=p.getViewport(qe);else{let le=d.getViewSubImage(h,qe);ue=le.viewport,R===0&&(e.setRenderTargetTextures(y,le.colorTexture,le.depthStencilTexture),e.setRenderTarget(y))}let ye=T[R];ye===void 0&&(ye=new Dt,ye.layers.enable(R),ye.viewport=new xt,T[R]=ye),ye.matrix.fromArray(qe.transform.matrix),ye.matrix.decompose(ye.position,ye.quaternion,ye.scale),ye.projectionMatrix.fromArray(qe.projectionMatrix),ye.projectionMatrixInverse.copy(ye.projectionMatrix).invert(),ye.viewport.set(ue.x,ue.y,ue.width,ue.height),R===0&&(P.matrix.copy(ye.matrix),P.matrix.decompose(P.position,P.quaternion,P.scale)),ae===!0&&P.cameras.push(ye)}let pe=r.enabledFeatures;if(pe&&pe.includes("depth-sensing")&&r.depthUsage=="gpu-optimized"&&x){d=n.getBinding();let R=d.getDepthInformation(Y[0]);R&&R.isValid&&R.texture&&m.init(R,r.renderState)}if(pe&&pe.includes("camera-access")&&x){e.state.unbindTexture(),d=n.getBinding();for(let R=0;R<Y.length;R++){let qe=Y[R].camera;if(qe){let ue=f[qe];ue||(ue=new ns,f[qe]=ue);let ye=d.getCameraImage(qe);ue.sourceTexture=ye}}}}for(let Y=0;Y<C.length;Y++){let ae=A[Y],pe=C[Y];ae!==null&&pe!==void 0&&pe.update(ae,J,l||a)}Oe&&Oe(X,J),J.detectedPlanes&&n.dispatchEvent({type:"planesdetected",data:J}),g=null}let Pe=new Pu;Pe.setAnimationLoop($e),this.setAnimationLoop=function(X){Oe=X},this.dispose=function(){}}},Di=new en,Z0=new ht;function J0(i,e){function t(m,f){m.matrixAutoUpdate===!0&&m.updateMatrix(),f.value.copy(m.matrix)}function n(m,f){f.color.getRGB(m.fogColor.value,ql(i)),f.isFog?(m.fogNear.value=f.near,m.fogFar.value=f.far):f.isFogExp2&&(m.fogDensity.value=f.density)}function r(m,f,S,M,y){f.isMeshBasicMaterial||f.isMeshLambertMaterial?s(m,f):f.isMeshToonMaterial?(s(m,f),d(m,f)):f.isMeshPhongMaterial?(s(m,f),u(m,f)):f.isMeshStandardMaterial?(s(m,f),h(m,f),f.isMeshPhysicalMaterial&&p(m,f,y)):f.isMeshMatcapMaterial?(s(m,f),g(m,f)):f.isMeshDepthMaterial?s(m,f):f.isMeshDistanceMaterial?(s(m,f),x(m,f)):f.isMeshNormalMaterial?s(m,f):f.isLineBasicMaterial?(a(m,f),f.isLineDashedMaterial&&o(m,f)):f.isPointsMaterial?c(m,f,S,M):f.isSpriteMaterial?l(m,f):f.isShadowMaterial?(m.color.value.copy(f.color),m.opacity.value=f.opacity):f.isShaderMaterial&&(f.uniformsNeedUpdate=!1)}function s(m,f){m.opacity.value=f.opacity,f.color&&m.diffuse.value.copy(f.color),f.emissive&&m.emissive.value.copy(f.emissive).multiplyScalar(f.emissiveIntensity),f.map&&(m.map.value=f.map,t(f.map,m.mapTransform)),f.alphaMap&&(m.alphaMap.value=f.alphaMap,t(f.alphaMap,m.alphaMapTransform)),f.bumpMap&&(m.bumpMap.value=f.bumpMap,t(f.bumpMap,m.bumpMapTransform),m.bumpScale.value=f.bumpScale,f.side===zt&&(m.bumpScale.value*=-1)),f.normalMap&&(m.normalMap.value=f.normalMap,t(f.normalMap,m.normalMapTransform),m.normalScale.value.copy(f.normalScale),f.side===zt&&m.normalScale.value.negate()),f.displacementMap&&(m.displacementMap.value=f.displacementMap,t(f.displacementMap,m.displacementMapTransform),m.displacementScale.value=f.displacementScale,m.displacementBias.value=f.displacementBias),f.emissiveMap&&(m.emissiveMap.value=f.emissiveMap,t(f.emissiveMap,m.emissiveMapTransform)),f.specularMap&&(m.specularMap.value=f.specularMap,t(f.specularMap,m.specularMapTransform)),f.alphaTest>0&&(m.alphaTest.value=f.alphaTest);let S=e.get(f),M=S.envMap,y=S.envMapRotation;M&&(m.envMap.value=M,Di.copy(y),Di.x*=-1,Di.y*=-1,Di.z*=-1,M.isCubeTexture&&M.isRenderTargetTexture===!1&&(Di.y*=-1,Di.z*=-1),m.envMapRotation.value.setFromMatrix4(Z0.makeRotationFromEuler(Di)),m.flipEnvMap.value=M.isCubeTexture&&M.isRenderTargetTexture===!1?-1:1,m.reflectivity.value=f.reflectivity,m.ior.value=f.ior,m.refractionRatio.value=f.refractionRatio),f.lightMap&&(m.lightMap.value=f.lightMap,m.lightMapIntensity.value=f.lightMapIntensity,t(f.lightMap,m.lightMapTransform)),f.aoMap&&(m.aoMap.value=f.aoMap,m.aoMapIntensity.value=f.aoMapIntensity,t(f.aoMap,m.aoMapTransform))}function a(m,f){m.diffuse.value.copy(f.color),m.opacity.value=f.opacity,f.map&&(m.map.value=f.map,t(f.map,m.mapTransform))}function o(m,f){m.dashSize.value=f.dashSize,m.totalSize.value=f.dashSize+f.gapSize,m.scale.value=f.scale}function c(m,f,S,M){m.diffuse.value.copy(f.color),m.opacity.value=f.opacity,m.size.value=f.size*S,m.scale.value=M*.5,f.map&&(m.map.value=f.map,t(f.map,m.uvTransform)),f.alphaMap&&(m.alphaMap.value=f.alphaMap,t(f.alphaMap,m.alphaMapTransform)),f.alphaTest>0&&(m.alphaTest.value=f.alphaTest)}function l(m,f){m.diffuse.value.copy(f.color),m.opacity.value=f.opacity,m.rotation.value=f.rotation,f.map&&(m.map.value=f.map,t(f.map,m.mapTransform)),f.alphaMap&&(m.alphaMap.value=f.alphaMap,t(f.alphaMap,m.alphaMapTransform)),f.alphaTest>0&&(m.alphaTest.value=f.alphaTest)}function u(m,f){m.specular.value.copy(f.specular),m.shininess.value=Math.max(f.shininess,1e-4)}function d(m,f){f.gradientMap&&(m.gradientMap.value=f.gradientMap)}function h(m,f){m.metalness.value=f.metalness,f.metalnessMap&&(m.metalnessMap.value=f.metalnessMap,t(f.metalnessMap,m.metalnessMapTransform)),m.roughness.value=f.roughness,f.roughnessMap&&(m.roughnessMap.value=f.roughnessMap,t(f.roughnessMap,m.roughnessMapTransform)),f.envMap&&(m.envMapIntensity.value=f.envMapIntensity)}function p(m,f,S){m.ior.value=f.ior,f.sheen>0&&(m.sheenColor.value.copy(f.sheenColor).multiplyScalar(f.sheen),m.sheenRoughness.value=f.sheenRoughness,f.sheenColorMap&&(m.sheenColorMap.value=f.sheenColorMap,t(f.sheenColorMap,m.sheenColorMapTransform)),f.sheenRoughnessMap&&(m.sheenRoughnessMap.value=f.sheenRoughnessMap,t(f.sheenRoughnessMap,m.sheenRoughnessMapTransform))),f.clearcoat>0&&(m.clearcoat.value=f.clearcoat,m.clearcoatRoughness.value=f.clearcoatRoughness,f.clearcoatMap&&(m.clearcoatMap.value=f.clearcoatMap,t(f.clearcoatMap,m.clearcoatMapTransform)),f.clearcoatRoughnessMap&&(m.clearcoatRoughnessMap.value=f.clearcoatRoughnessMap,t(f.clearcoatRoughnessMap,m.clearcoatRoughnessMapTransform)),f.clearcoatNormalMap&&(m.clearcoatNormalMap.value=f.clearcoatNormalMap,t(f.clearcoatNormalMap,m.clearcoatNormalMapTransform),m.clearcoatNormalScale.value.copy(f.clearcoatNormalScale),f.side===zt&&m.clearcoatNormalScale.value.negate())),f.dispersion>0&&(m.dispersion.value=f.dispersion),f.iridescence>0&&(m.iridescence.value=f.iridescence,m.iridescenceIOR.value=f.iridescenceIOR,m.iridescenceThicknessMinimum.value=f.iridescenceThicknessRange[0],m.iridescenceThicknessMaximum.value=f.iridescenceThicknessRange[1],f.iridescenceMap&&(m.iridescenceMap.value=f.iridescenceMap,t(f.iridescenceMap,m.iridescenceMapTransform)),f.iridescenceThicknessMap&&(m.iridescenceThicknessMap.value=f.iridescenceThicknessMap,t(f.iridescenceThicknessMap,m.iridescenceThicknessMapTransform))),f.transmission>0&&(m.transmission.value=f.transmission,m.transmissionSamplerMap.value=S.texture,m.transmissionSamplerSize.value.set(S.width,S.height),f.transmissionMap&&(m.transmissionMap.value=f.transmissionMap,t(f.transmissionMap,m.transmissionMapTransform)),m.thickness.value=f.thickness,f.thicknessMap&&(m.thicknessMap.value=f.thicknessMap,t(f.thicknessMap,m.thicknessMapTransform)),m.attenuationDistance.value=f.attenuationDistance,m.attenuationColor.value.copy(f.attenuationColor)),f.anisotropy>0&&(m.anisotropyVector.value.set(f.anisotropy*Math.cos(f.anisotropyRotation),f.anisotropy*Math.sin(f.anisotropyRotation)),f.anisotropyMap&&(m.anisotropyMap.value=f.anisotropyMap,t(f.anisotropyMap,m.anisotropyMapTransform))),m.specularIntensity.value=f.specularIntensity,m.specularColor.value.copy(f.specularColor),f.specularColorMap&&(m.specularColorMap.value=f.specularColorMap,t(f.specularColorMap,m.specularColorMapTransform)),f.specularIntensityMap&&(m.specularIntensityMap.value=f.specularIntensityMap,t(f.specularIntensityMap,m.specularIntensityMapTransform))}function g(m,f){f.matcap&&(m.matcap.value=f.matcap)}function x(m,f){let S=e.get(f).light;m.referencePosition.value.setFromMatrixPosition(S.matrixWorld),m.nearDistance.value=S.shadow.camera.near,m.farDistance.value=S.shadow.camera.far}return{refreshFogUniforms:n,refreshMaterialUniforms:r}}function K0(i,e,t,n){let r={},s={},a=[],o=i.getParameter(i.MAX_UNIFORM_BUFFER_BINDINGS);function c(S,M){let y=M.program;n.uniformBlockBinding(S,y)}function l(S,M){let y=r[S.id];y===void 0&&(g(S),y=u(S),r[S.id]=y,S.addEventListener("dispose",m));let C=M.program;n.updateUBOMapping(S,C);let A=e.render.frame;s[S.id]!==A&&(h(S),s[S.id]=A)}function u(S){let M=d();S.__bindingPointIndex=M;let y=i.createBuffer(),C=S.__size,A=S.usage;return i.bindBuffer(i.UNIFORM_BUFFER,y),i.bufferData(i.UNIFORM_BUFFER,C,A),i.bindBuffer(i.UNIFORM_BUFFER,null),i.bindBufferBase(i.UNIFORM_BUFFER,M,y),y}function d(){for(let S=0;S<o;S++)if(a.indexOf(S)===-1)return a.push(S),S;return console.error("THREE.WebGLRenderer: Maximum number of simultaneously usable uniforms groups reached."),0}function h(S){let M=r[S.id],y=S.uniforms,C=S.__cache;i.bindBuffer(i.UNIFORM_BUFFER,M);for(let A=0,I=y.length;A<I;A++){let N=Array.isArray(y[A])?y[A]:[y[A]];for(let v=0,b=N.length;v<b;v++){let T=N[v];if(p(T,A,v,C)===!0){let P=T.__offset,U=Array.isArray(T.value)?T.value:[T.value],F=0;for(let k=0;k<U.length;k++){let G=U[k],K=x(G);typeof G=="number"||typeof G=="boolean"?(T.__data[0]=G,i.bufferSubData(i.UNIFORM_BUFFER,P+F,T.__data)):G.isMatrix3?(T.__data[0]=G.elements[0],T.__data[1]=G.elements[1],T.__data[2]=G.elements[2],T.__data[3]=0,T.__data[4]=G.elements[3],T.__data[5]=G.elements[4],T.__data[6]=G.elements[5],T.__data[7]=0,T.__data[8]=G.elements[6],T.__data[9]=G.elements[7],T.__data[10]=G.elements[8],T.__data[11]=0):(G.toArray(T.__data,F),F+=K.storage/Float32Array.BYTES_PER_ELEMENT)}i.bufferSubData(i.UNIFORM_BUFFER,P,T.__data)}}}i.bindBuffer(i.UNIFORM_BUFFER,null)}function p(S,M,y,C){let A=S.value,I=M+"_"+y;if(C[I]===void 0)return typeof A=="number"||typeof A=="boolean"?C[I]=A:C[I]=A.clone(),!0;{let N=C[I];if(typeof A=="number"||typeof A=="boolean"){if(N!==A)return C[I]=A,!0}else if(N.equals(A)===!1)return N.copy(A),!0}return!1}function g(S){let M=S.uniforms,y=0,C=16;for(let I=0,N=M.length;I<N;I++){let v=Array.isArray(M[I])?M[I]:[M[I]];for(let b=0,T=v.length;b<T;b++){let P=v[b],U=Array.isArray(P.value)?P.value:[P.value];for(let F=0,k=U.length;F<k;F++){let G=U[F],K=x(G),W=y%C,se=W%K.boundary,de=W+se;y+=se,de!==0&&C-de<K.storage&&(y+=C-de),P.__data=new Float32Array(K.storage/Float32Array.BYTES_PER_ELEMENT),P.__offset=y,y+=K.storage}}}let A=y%C;return A>0&&(y+=C-A),S.__size=y,S.__cache={},this}function x(S){let M={boundary:0,storage:0};return typeof S=="number"||typeof S=="boolean"?(M.boundary=4,M.storage=4):S.isVector2?(M.boundary=8,M.storage=8):S.isVector3||S.isColor?(M.boundary=16,M.storage=12):S.isVector4?(M.boundary=16,M.storage=16):S.isMatrix3?(M.boundary=48,M.storage=48):S.isMatrix4?(M.boundary=64,M.storage=64):S.isTexture?console.warn("THREE.WebGLRenderer: Texture samplers can not be part of an uniforms group."):console.warn("THREE.WebGLRenderer: Unsupported uniform value type.",S),M}function m(S){let M=S.target;M.removeEventListener("dispose",m);let y=a.indexOf(M.__bindingPointIndex);a.splice(y,1),i.deleteBuffer(r[M.id]),delete r[M.id],delete s[M.id]}function f(){for(let S in r)i.deleteBuffer(r[S]);a=[],r={},s={}}return{bind:c,update:l,dispose:f}}var Co=class{constructor(e={}){let{canvas:t=nu(),context:n=null,depth:r=!0,stencil:s=!1,alpha:a=!1,antialias:o=!1,premultipliedAlpha:c=!0,preserveDrawingBuffer:l=!1,powerPreference:u="default",failIfMajorPerformanceCaveat:d=!1,reversedDepthBuffer:h=!1}=e;this.isWebGLRenderer=!0;let p;if(n!==null){if(typeof WebGLRenderingContext<"u"&&n instanceof WebGLRenderingContext)throw new Error("THREE.WebGLRenderer: WebGL 1 is not supported since r163.");p=n.getContextAttributes().alpha}else p=a;let g=new Uint32Array(4),x=new Int32Array(4),m=null,f=null,S=[],M=[];this.domElement=t,this.debug={checkShaderErrors:!0,onShaderError:null},this.autoClear=!0,this.autoClearColor=!0,this.autoClearDepth=!0,this.autoClearStencil=!0,this.sortObjects=!0,this.clippingPlanes=[],this.localClippingEnabled=!1,this.toneMapping=qn,this.toneMappingExposure=1,this.transmissionResolutionScale=1;let y=this,C=!1;this._outputColorSpace=Nt;let A=0,I=0,N=null,v=-1,b=null,T=new xt,P=new xt,U=null,F=new Be(0),k=0,G=t.width,K=t.height,W=1,se=null,de=null,Ae=new xt(0,0,G,K),fe=new xt(0,0,G,K),Oe=!1,$e=new gr,Pe=!1,X=!1,J=new ht,Y=new D,ae=new xt,pe={background:null,fog:null,environment:null,overrideMaterial:null,isScene:!0},Ce=!1;function it(){return N===null?W:1}let R=n;function qe(w,O){return t.getContext(w,O)}try{let w={alpha:!0,depth:r,stencil:s,antialias:o,premultipliedAlpha:c,preserveDrawingBuffer:l,powerPreference:u,failIfMajorPerformanceCaveat:d};if("setAttribute"in t&&t.setAttribute("data-engine",`three.js r${"180"}`),t.addEventListener("webglcontextlost",oe,!1),t.addEventListener("webglcontextrestored",Me,!1),t.addEventListener("webglcontextcreationerror",te,!1),R===null){let O="webgl2";if(R=qe(O,w),R===null)throw qe(O)?new Error("Error creating WebGL context with your selected attributes."):new Error("Error creating WebGL context.")}}catch(w){throw console.error("THREE.WebGLRenderer: "+w.message),w}let ue,ye,le,Je,_e,He,Re,Ve,E,_,z,q,j,$,Se,re,be,we,ee,ge,Fe,Ie,he,Ge;function L(){ue=new mg(R),ue.init(),Ie=new $0(R,ue),ye=new lg(R,ue,e,Ie),le=new W0(R,ue),ye.reversedDepthBuffer&&h&&le.buffers.depth.setReversed(!0),Je=new _g(R),_e=new P0,He=new X0(R,ue,le,_e,ye,Ie,Je),Re=new dg(y),Ve=new pg(y),E=new Sf(R),he=new ag(R,E),_=new gg(R,E,Je,he),z=new vg(R,_,E,Je),ee=new yg(R,ye,He),re=new cg(_e),q=new I0(y,Re,Ve,ue,ye,he,re),j=new J0(y,_e),$=new D0,Se=new z0(ue),we=new sg(y,Re,Ve,le,z,p,c),be=new V0(y,z,ye),Ge=new K0(R,Je,ye,le),ge=new og(R,ue,Je),Fe=new xg(R,ue,Je),Je.programs=q.programs,y.capabilities=ye,y.extensions=ue,y.properties=_e,y.renderLists=$,y.shadowMap=be,y.state=le,y.info=Je}L();let ie=new dc(y,R);this.xr=ie,this.getContext=function(){return R},this.getContextAttributes=function(){return R.getContextAttributes()},this.forceContextLoss=function(){let w=ue.get("WEBGL_lose_context");w&&w.loseContext()},this.forceContextRestore=function(){let w=ue.get("WEBGL_lose_context");w&&w.restoreContext()},this.getPixelRatio=function(){return W},this.setPixelRatio=function(w){w!==void 0&&(W=w,this.setSize(G,K,!1))},this.getSize=function(w){return w.set(G,K)},this.setSize=function(w,O,H=!0){if(ie.isPresenting){console.warn("THREE.WebGLRenderer: Can't change size while VR device is presenting.");return}G=w,K=O,t.width=Math.floor(w*W),t.height=Math.floor(O*W),H===!0&&(t.style.width=w+"px",t.style.height=O+"px"),this.setViewport(0,0,w,O)},this.getDrawingBufferSize=function(w){return w.set(G*W,K*W).floor()},this.setDrawingBufferSize=function(w,O,H){G=w,K=O,W=H,t.width=Math.floor(w*H),t.height=Math.floor(O*H),this.setViewport(0,0,w,O)},this.getCurrentViewport=function(w){return w.copy(T)},this.getViewport=function(w){return w.copy(Ae)},this.setViewport=function(w,O,H,V){w.isVector4?Ae.set(w.x,w.y,w.z,w.w):Ae.set(w,O,H,V),le.viewport(T.copy(Ae).multiplyScalar(W).round())},this.getScissor=function(w){return w.copy(fe)},this.setScissor=function(w,O,H,V){w.isVector4?fe.set(w.x,w.y,w.z,w.w):fe.set(w,O,H,V),le.scissor(P.copy(fe).multiplyScalar(W).round())},this.getScissorTest=function(){return Oe},this.setScissorTest=function(w){le.setScissorTest(Oe=w)},this.setOpaqueSort=function(w){se=w},this.setTransparentSort=function(w){de=w},this.getClearColor=function(w){return w.copy(we.getClearColor())},this.setClearColor=function(){we.setClearColor(...arguments)},this.getClearAlpha=function(){return we.getClearAlpha()},this.setClearAlpha=function(){we.setClearAlpha(...arguments)},this.clear=function(w=!0,O=!0,H=!0){let V=0;if(w){let B=!1;if(N!==null){let ne=N.texture.format;B=ne===Ya||ne===qa||ne===$a}if(B){let ne=N.texture.type,me=ne===Sn||ne===pi||ne===_r||ne===vr||ne===Wa||ne===Xa,Ee=we.getClearColor(),ve=we.getClearAlpha(),Le=Ee.r,Ue=Ee.g,Ne=Ee.b;me?(g[0]=Le,g[1]=Ue,g[2]=Ne,g[3]=ve,R.clearBufferuiv(R.COLOR,0,g)):(x[0]=Le,x[1]=Ue,x[2]=Ne,x[3]=ve,R.clearBufferiv(R.COLOR,0,x))}else V|=R.COLOR_BUFFER_BIT}O&&(V|=R.DEPTH_BUFFER_BIT),H&&(V|=R.STENCIL_BUFFER_BIT,this.state.buffers.stencil.setMask(4294967295)),R.clear(V)},this.clearColor=function(){this.clear(!0,!1,!1)},this.clearDepth=function(){this.clear(!1,!0,!1)},this.clearStencil=function(){this.clear(!1,!1,!0)},this.dispose=function(){t.removeEventListener("webglcontextlost",oe,!1),t.removeEventListener("webglcontextrestored",Me,!1),t.removeEventListener("webglcontextcreationerror",te,!1),we.dispose(),$.dispose(),Se.dispose(),_e.dispose(),Re.dispose(),Ve.dispose(),z.dispose(),he.dispose(),Ge.dispose(),q.dispose(),ie.dispose(),ie.removeEventListener("sessionstart",Tn),ie.removeEventListener("sessionend",Lc),xi.stop()};function oe(w){w.preventDefault(),console.log("THREE.WebGLRenderer: Context Lost."),C=!0}function Me(){console.log("THREE.WebGLRenderer: Context Restored."),C=!1;let w=Je.autoReset,O=be.enabled,H=be.autoUpdate,V=be.needsUpdate,B=be.type;L(),Je.autoReset=w,be.enabled=O,be.autoUpdate=H,be.needsUpdate=V,be.type=B}function te(w){console.error("THREE.WebGLRenderer: A WebGL context could not be created. Reason: ",w.statusMessage)}function Z(w){let O=w.target;O.removeEventListener("dispose",Z),Te(O)}function Te(w){ze(w),_e.remove(w)}function ze(w){let O=_e.get(w).programs;O!==void 0&&(O.forEach(function(H){q.releaseProgram(H)}),w.isShaderMaterial&&q.releaseShaderCache(w))}this.renderBufferDirect=function(w,O,H,V,B,ne){O===null&&(O=pe);let me=B.isMesh&&B.matrixWorld.determinant()<0,Ee=Mh(w,O,H,V,B);le.setMaterial(V,me);let ve=H.index,Le=1;if(V.wireframe===!0){if(ve=_.getWireframeAttribute(H),ve===void 0)return;Le=2}let Ue=H.drawRange,Ne=H.attributes.position,Ze=Ue.start*Le,rt=(Ue.start+Ue.count)*Le;ne!==null&&(Ze=Math.max(Ze,ne.start*Le),rt=Math.min(rt,(ne.start+ne.count)*Le)),ve!==null?(Ze=Math.max(Ze,0),rt=Math.min(rt,ve.count)):Ne!=null&&(Ze=Math.max(Ze,0),rt=Math.min(rt,Ne.count));let vt=rt-Ze;if(vt<0||vt===1/0)return;he.setup(B,V,Ee,H,ve);let lt,st=ge;if(ve!==null&&(lt=E.get(ve),st=Fe,st.setIndex(lt)),B.isMesh)V.wireframe===!0?(le.setLineWidth(V.wireframeLinewidth*it()),st.setMode(R.LINES)):st.setMode(R.TRIANGLES);else if(B.isLine){let De=V.linewidth;De===void 0&&(De=1),le.setLineWidth(De*it()),B.isLineSegments?st.setMode(R.LINES):B.isLineLoop?st.setMode(R.LINE_LOOP):st.setMode(R.LINE_STRIP)}else B.isPoints?st.setMode(R.POINTS):B.isSprite&&st.setMode(R.TRIANGLES);if(B.isBatchedMesh)if(B._multiDrawInstances!==null)ur("THREE.WebGLRenderer: renderMultiDrawInstances has been deprecated and will be removed in r184. Append to renderMultiDraw arguments and use indirection."),st.renderMultiDrawInstances(B._multiDrawStarts,B._multiDrawCounts,B._multiDrawCount,B._multiDrawInstances);else if(ue.get("WEBGL_multi_draw"))st.renderMultiDraw(B._multiDrawStarts,B._multiDrawCounts,B._multiDrawCount);else{let De=B._multiDrawStarts,mt=B._multiDrawCounts,je=B._multiDrawCount,Jt=ve?E.get(ve).bytesPerElement:1,Wi=_e.get(V).currentProgram.getUniforms();for(let Kt=0;Kt<je;Kt++)Wi.setValue(R,"_gl_DrawID",Kt),st.render(De[Kt]/Jt,mt[Kt])}else if(B.isInstancedMesh)st.renderInstances(Ze,vt,B.count);else if(H.isInstancedBufferGeometry){let De=H._maxInstanceCount!==void 0?H._maxInstanceCount:1/0,mt=Math.min(H.instanceCount,De);st.renderInstances(Ze,vt,mt)}else st.render(Ze,vt)};function ot(w,O,H){w.transparent===!0&&w.side===un&&w.forceSinglePass===!1?(w.side=zt,w.needsUpdate=!0,Rs(w,O,H),w.side=Gn,w.needsUpdate=!0,Rs(w,O,H),w.side=un):Rs(w,O,H)}this.compile=function(w,O,H=null){H===null&&(H=w),f=Se.get(H),f.init(O),M.push(f),H.traverseVisible(function(B){B.isLight&&B.layers.test(O.layers)&&(f.pushLight(B),B.castShadow&&f.pushShadow(B))}),w!==H&&w.traverseVisible(function(B){B.isLight&&B.layers.test(O.layers)&&(f.pushLight(B),B.castShadow&&f.pushShadow(B))}),f.setupLights();let V=new Set;return w.traverse(function(B){if(!(B.isMesh||B.isPoints||B.isLine||B.isSprite))return;let ne=B.material;if(ne)if(Array.isArray(ne))for(let me=0;me<ne.length;me++){let Ee=ne[me];ot(Ee,H,B),V.add(Ee)}else ot(ne,H,B),V.add(ne)}),f=M.pop(),V},this.compileAsync=function(w,O,H=null){let V=this.compile(w,O,H);return new Promise(B=>{function ne(){if(V.forEach(function(me){_e.get(me).currentProgram.isReady()&&V.delete(me)}),V.size===0){B(w);return}setTimeout(ne,10)}ue.get("KHR_parallel_shader_compile")!==null?ne():setTimeout(ne,10)})};let Qe=null;function Fn(w){Qe&&Qe(w)}function Tn(){xi.stop()}function Lc(){xi.start()}let xi=new Pu;xi.setAnimationLoop(Fn),typeof self<"u"&&xi.setContext(self),this.setAnimationLoop=function(w){Qe=w,ie.setAnimationLoop(w),w===null?xi.stop():xi.start()},ie.addEventListener("sessionstart",Tn),ie.addEventListener("sessionend",Lc),this.render=function(w,O){if(O!==void 0&&O.isCamera!==!0){console.error("THREE.WebGLRenderer.render: camera is not an instance of THREE.Camera.");return}if(C===!0)return;if(w.matrixWorldAutoUpdate===!0&&w.updateMatrixWorld(),O.parent===null&&O.matrixWorldAutoUpdate===!0&&O.updateMatrixWorld(),ie.enabled===!0&&ie.isPresenting===!0&&(ie.cameraAutoUpdate===!0&&ie.updateCamera(O),O=ie.getCamera()),w.isScene===!0&&w.onBeforeRender(y,w,O,N),f=Se.get(w,M.length),f.init(O),M.push(f),J.multiplyMatrices(O.projectionMatrix,O.matrixWorldInverse),$e.setFromProjectionMatrix(J,vn,O.reversedDepth),X=this.localClippingEnabled,Pe=re.init(this.clippingPlanes,X),m=$.get(w,S.length),m.init(),S.push(m),ie.enabled===!0&&ie.isPresenting===!0){let ne=y.xr.getDepthSensingMesh();ne!==null&&Xo(ne,O,-1/0,y.sortObjects)}Xo(w,O,0,y.sortObjects),m.finish(),y.sortObjects===!0&&m.sort(se,de),Ce=ie.enabled===!1||ie.isPresenting===!1||ie.hasDepthSensing()===!1,Ce&&we.addToRenderList(m,w),this.info.render.frame++,Pe===!0&&re.beginShadows();let H=f.state.shadowsArray;be.render(H,w,O),Pe===!0&&re.endShadows(),this.info.autoReset===!0&&this.info.reset();let V=m.opaque,B=m.transmissive;if(f.setupLights(),O.isArrayCamera){let ne=O.cameras;if(B.length>0)for(let me=0,Ee=ne.length;me<Ee;me++){let ve=ne[me];Uc(V,B,w,ve)}Ce&&we.render(w);for(let me=0,Ee=ne.length;me<Ee;me++){let ve=ne[me];Fc(m,w,ve,ve.viewport)}}else B.length>0&&Uc(V,B,w,O),Ce&&we.render(w),Fc(m,w,O);N!==null&&I===0&&(He.updateMultisampleRenderTarget(N),He.updateRenderTargetMipmap(N)),w.isScene===!0&&w.onAfterRender(y,w,O),he.resetDefaultState(),v=-1,b=null,M.pop(),M.length>0?(f=M[M.length-1],Pe===!0&&re.setGlobalState(y.clippingPlanes,f.state.camera)):f=null,S.pop(),S.length>0?m=S[S.length-1]:m=null};function Xo(w,O,H,V){if(w.visible===!1)return;if(w.layers.test(O.layers)){if(w.isGroup)H=w.renderOrder;else if(w.isLOD)w.autoUpdate===!0&&w.update(O);else if(w.isLight)f.pushLight(w),w.castShadow&&f.pushShadow(w);else if(w.isSprite){if(!w.frustumCulled||$e.intersectsSprite(w)){V&&ae.setFromMatrixPosition(w.matrixWorld).applyMatrix4(J);let me=z.update(w),Ee=w.material;Ee.visible&&m.push(w,me,Ee,H,ae.z,null)}}else if((w.isMesh||w.isLine||w.isPoints)&&(!w.frustumCulled||$e.intersectsObject(w))){let me=z.update(w),Ee=w.material;if(V&&(w.boundingSphere!==void 0?(w.boundingSphere===null&&w.computeBoundingSphere(),ae.copy(w.boundingSphere.center)):(me.boundingSphere===null&&me.computeBoundingSphere(),ae.copy(me.boundingSphere.center)),ae.applyMatrix4(w.matrixWorld).applyMatrix4(J)),Array.isArray(Ee)){let ve=me.groups;for(let Le=0,Ue=ve.length;Le<Ue;Le++){let Ne=ve[Le],Ze=Ee[Ne.materialIndex];Ze&&Ze.visible&&m.push(w,me,Ze,H,ae.z,Ne)}}else Ee.visible&&m.push(w,me,Ee,H,ae.z,null)}}let ne=w.children;for(let me=0,Ee=ne.length;me<Ee;me++)Xo(ne[me],O,H,V)}function Fc(w,O,H,V){let B=w.opaque,ne=w.transmissive,me=w.transparent;f.setupLightsView(H),Pe===!0&&re.setGlobalState(y.clippingPlanes,H),V&&le.viewport(T.copy(V)),B.length>0&&Cs(B,O,H),ne.length>0&&Cs(ne,O,H),me.length>0&&Cs(me,O,H),le.buffers.depth.setTest(!0),le.buffers.depth.setMask(!0),le.buffers.color.setMask(!0),le.setPolygonOffset(!1)}function Uc(w,O,H,V){if((H.isScene===!0?H.overrideMaterial:null)!==null)return;f.state.transmissionRenderTarget[V.id]===void 0&&(f.state.transmissionRenderTarget[V.id]=new Rn(1,1,{generateMipmaps:!0,type:ue.has("EXT_color_buffer_half_float")||ue.has("EXT_color_buffer_float")?yr:Sn,minFilter:fi,samples:4,stencilBuffer:s,resolveDepthBuffer:!1,resolveStencilBuffer:!1,colorSpace:Ke.workingColorSpace}));let ne=f.state.transmissionRenderTarget[V.id],me=V.viewport||T;ne.setSize(me.z*y.transmissionResolutionScale,me.w*y.transmissionResolutionScale);let Ee=y.getRenderTarget(),ve=y.getActiveCubeFace(),Le=y.getActiveMipmapLevel();y.setRenderTarget(ne),y.getClearColor(F),k=y.getClearAlpha(),k<1&&y.setClearColor(16777215,.5),y.clear(),Ce&&we.render(H);let Ue=y.toneMapping;y.toneMapping=qn;let Ne=V.viewport;if(V.viewport!==void 0&&(V.viewport=void 0),f.setupLightsView(V),Pe===!0&&re.setGlobalState(y.clippingPlanes,V),Cs(w,H,V),He.updateMultisampleRenderTarget(ne),He.updateRenderTargetMipmap(ne),ue.has("WEBGL_multisampled_render_to_texture")===!1){let Ze=!1;for(let rt=0,vt=O.length;rt<vt;rt++){let lt=O[rt],st=lt.object,De=lt.geometry,mt=lt.material,je=lt.group;if(mt.side===un&&st.layers.test(V.layers)){let Jt=mt.side;mt.side=zt,mt.needsUpdate=!0,Oc(st,H,V,De,mt,je),mt.side=Jt,mt.needsUpdate=!0,Ze=!0}}Ze===!0&&(He.updateMultisampleRenderTarget(ne),He.updateRenderTargetMipmap(ne))}y.setRenderTarget(Ee,ve,Le),y.setClearColor(F,k),Ne!==void 0&&(V.viewport=Ne),y.toneMapping=Ue}function Cs(w,O,H){let V=O.isScene===!0?O.overrideMaterial:null;for(let B=0,ne=w.length;B<ne;B++){let me=w[B],Ee=me.object,ve=me.geometry,Le=me.group,Ue=me.material;Ue.allowOverride===!0&&V!==null&&(Ue=V),Ee.layers.test(H.layers)&&Oc(Ee,O,H,ve,Ue,Le)}}function Oc(w,O,H,V,B,ne){w.onBeforeRender(y,O,H,V,B,ne),w.modelViewMatrix.multiplyMatrices(H.matrixWorldInverse,w.matrixWorld),w.normalMatrix.getNormalMatrix(w.modelViewMatrix),B.onBeforeRender(y,O,H,V,w,ne),B.transparent===!0&&B.side===un&&B.forceSinglePass===!1?(B.side=zt,B.needsUpdate=!0,y.renderBufferDirect(H,O,V,B,w,ne),B.side=Gn,B.needsUpdate=!0,y.renderBufferDirect(H,O,V,B,w,ne),B.side=un):y.renderBufferDirect(H,O,V,B,w,ne),w.onAfterRender(y,O,H,V,B,ne)}function Rs(w,O,H){O.isScene!==!0&&(O=pe);let V=_e.get(w),B=f.state.lights,ne=f.state.shadowsArray,me=B.state.version,Ee=q.getParameters(w,B.state,ne,O,H),ve=q.getProgramCacheKey(Ee),Le=V.programs;V.environment=w.isMeshStandardMaterial?O.environment:null,V.fog=O.fog,V.envMap=(w.isMeshStandardMaterial?Ve:Re).get(w.envMap||V.environment),V.envMapRotation=V.environment!==null&&w.envMap===null?O.environmentRotation:w.envMapRotation,Le===void 0&&(w.addEventListener("dispose",Z),Le=new Map,V.programs=Le);let Ue=Le.get(ve);if(Ue!==void 0){if(V.currentProgram===Ue&&V.lightsStateVersion===me)return zc(w,Ee),Ue}else Ee.uniforms=q.getUniforms(w),w.onBeforeCompile(Ee,y),Ue=q.acquireProgram(Ee,ve),Le.set(ve,Ue),V.uniforms=Ee.uniforms;let Ne=V.uniforms;return(!w.isShaderMaterial&&!w.isRawShaderMaterial||w.clipping===!0)&&(Ne.clippingPlanes=re.uniform),zc(w,Ee),V.needsLights=Eh(w),V.lightsStateVersion=me,V.needsLights&&(Ne.ambientLightColor.value=B.state.ambient,Ne.lightProbe.value=B.state.probe,Ne.directionalLights.value=B.state.directional,Ne.directionalLightShadows.value=B.state.directionalShadow,Ne.spotLights.value=B.state.spot,Ne.spotLightShadows.value=B.state.spotShadow,Ne.rectAreaLights.value=B.state.rectArea,Ne.ltc_1.value=B.state.rectAreaLTC1,Ne.ltc_2.value=B.state.rectAreaLTC2,Ne.pointLights.value=B.state.point,Ne.pointLightShadows.value=B.state.pointShadow,Ne.hemisphereLights.value=B.state.hemi,Ne.directionalShadowMap.value=B.state.directionalShadowMap,Ne.directionalShadowMatrix.value=B.state.directionalShadowMatrix,Ne.spotShadowMap.value=B.state.spotShadowMap,Ne.spotLightMatrix.value=B.state.spotLightMatrix,Ne.spotLightMap.value=B.state.spotLightMap,Ne.pointShadowMap.value=B.state.pointShadowMap,Ne.pointShadowMatrix.value=B.state.pointShadowMatrix),V.currentProgram=Ue,V.uniformsList=null,Ue}function Bc(w){if(w.uniformsList===null){let O=w.currentProgram.getUniforms();w.uniformsList=Sr.seqWithValue(O.seq,w.uniforms)}return w.uniformsList}function zc(w,O){let H=_e.get(w);H.outputColorSpace=O.outputColorSpace,H.batching=O.batching,H.batchingColor=O.batchingColor,H.instancing=O.instancing,H.instancingColor=O.instancingColor,H.instancingMorph=O.instancingMorph,H.skinning=O.skinning,H.morphTargets=O.morphTargets,H.morphNormals=O.morphNormals,H.morphColors=O.morphColors,H.morphTargetsCount=O.morphTargetsCount,H.numClippingPlanes=O.numClippingPlanes,H.numIntersection=O.numClipIntersection,H.vertexAlphas=O.vertexAlphas,H.vertexTangents=O.vertexTangents,H.toneMapping=O.toneMapping}function Mh(w,O,H,V,B){O.isScene!==!0&&(O=pe),He.resetTextureUnits();let ne=O.fog,me=V.isMeshStandardMaterial?O.environment:null,Ee=N===null?y.outputColorSpace:N.isXRRenderTarget===!0?N.texture.colorSpace:Ti,ve=(V.isMeshStandardMaterial?Ve:Re).get(V.envMap||me),Le=V.vertexColors===!0&&!!H.attributes.color&&H.attributes.color.itemSize===4,Ue=!!H.attributes.tangent&&(!!V.normalMap||V.anisotropy>0),Ne=!!H.morphAttributes.position,Ze=!!H.morphAttributes.normal,rt=!!H.morphAttributes.color,vt=qn;V.toneMapped&&(N===null||N.isXRRenderTarget===!0)&&(vt=y.toneMapping);let lt=H.morphAttributes.position||H.morphAttributes.normal||H.morphAttributes.color,st=lt!==void 0?lt.length:0,De=_e.get(V),mt=f.state.lights;if(Pe===!0&&(X===!0||w!==b)){let Ut=w===b&&V.id===v;re.setState(V,w,Ut)}let je=!1;V.version===De.__version?(De.needsLights&&De.lightsStateVersion!==mt.state.version||De.outputColorSpace!==Ee||B.isBatchedMesh&&De.batching===!1||!B.isBatchedMesh&&De.batching===!0||B.isBatchedMesh&&De.batchingColor===!0&&B.colorTexture===null||B.isBatchedMesh&&De.batchingColor===!1&&B.colorTexture!==null||B.isInstancedMesh&&De.instancing===!1||!B.isInstancedMesh&&De.instancing===!0||B.isSkinnedMesh&&De.skinning===!1||!B.isSkinnedMesh&&De.skinning===!0||B.isInstancedMesh&&De.instancingColor===!0&&B.instanceColor===null||B.isInstancedMesh&&De.instancingColor===!1&&B.instanceColor!==null||B.isInstancedMesh&&De.instancingMorph===!0&&B.morphTexture===null||B.isInstancedMesh&&De.instancingMorph===!1&&B.morphTexture!==null||De.envMap!==ve||V.fog===!0&&De.fog!==ne||De.numClippingPlanes!==void 0&&(De.numClippingPlanes!==re.numPlanes||De.numIntersection!==re.numIntersection)||De.vertexAlphas!==Le||De.vertexTangents!==Ue||De.morphTargets!==Ne||De.morphNormals!==Ze||De.morphColors!==rt||De.toneMapping!==vt||De.morphTargetsCount!==st)&&(je=!0):(je=!0,De.__version=V.version);let Jt=De.currentProgram;je===!0&&(Jt=Rs(V,O,B));let Wi=!1,Kt=!1,Ir=!1,gt=Jt.getUniforms(),on=De.uniforms;if(le.useProgram(Jt.program)&&(Wi=!0,Kt=!0,Ir=!0),V.id!==v&&(v=V.id,Kt=!0),Wi||b!==w){le.buffers.depth.getReversed()&&w.reversedDepth!==!0&&(w._reversedDepth=!0,w.updateProjectionMatrix()),gt.setValue(R,"projectionMatrix",w.projectionMatrix),gt.setValue(R,"viewMatrix",w.matrixWorldInverse);let Ht=gt.map.cameraPosition;Ht!==void 0&&Ht.setValue(R,Y.setFromMatrixPosition(w.matrixWorld)),ye.logarithmicDepthBuffer&&gt.setValue(R,"logDepthBufFC",2/(Math.log(w.far+1)/Math.LN2)),(V.isMeshPhongMaterial||V.isMeshToonMaterial||V.isMeshLambertMaterial||V.isMeshBasicMaterial||V.isMeshStandardMaterial||V.isShaderMaterial)&&gt.setValue(R,"isOrthographic",w.isOrthographicCamera===!0),b!==w&&(b=w,Kt=!0,Ir=!0)}if(B.isSkinnedMesh){gt.setOptional(R,B,"bindMatrix"),gt.setOptional(R,B,"bindMatrixInverse");let Ut=B.skeleton;Ut&&(Ut.boneTexture===null&&Ut.computeBoneTexture(),gt.setValue(R,"boneTexture",Ut.boneTexture,He))}B.isBatchedMesh&&(gt.setOptional(R,B,"batchingTexture"),gt.setValue(R,"batchingTexture",B._matricesTexture,He),gt.setOptional(R,B,"batchingIdTexture"),gt.setValue(R,"batchingIdTexture",B._indirectTexture,He),gt.setOptional(R,B,"batchingColorTexture"),B._colorsTexture!==null&&gt.setValue(R,"batchingColorTexture",B._colorsTexture,He));let ln=H.morphAttributes;if((ln.position!==void 0||ln.normal!==void 0||ln.color!==void 0)&&ee.update(B,H,Jt),(Kt||De.receiveShadow!==B.receiveShadow)&&(De.receiveShadow=B.receiveShadow,gt.setValue(R,"receiveShadow",B.receiveShadow)),V.isMeshGouraudMaterial&&V.envMap!==null&&(on.envMap.value=ve,on.flipEnvMap.value=ve.isCubeTexture&&ve.isRenderTargetTexture===!1?-1:1),V.isMeshStandardMaterial&&V.envMap===null&&O.environment!==null&&(on.envMapIntensity.value=O.environmentIntensity),Kt&&(gt.setValue(R,"toneMappingExposure",y.toneMappingExposure),De.needsLights&&Sh(on,Ir),ne&&V.fog===!0&&j.refreshFogUniforms(on,ne),j.refreshMaterialUniforms(on,V,W,K,f.state.transmissionRenderTarget[w.id]),Sr.upload(R,Bc(De),on,He)),V.isShaderMaterial&&V.uniformsNeedUpdate===!0&&(Sr.upload(R,Bc(De),on,He),V.uniformsNeedUpdate=!1),V.isSpriteMaterial&&gt.setValue(R,"center",B.center),gt.setValue(R,"modelViewMatrix",B.modelViewMatrix),gt.setValue(R,"normalMatrix",B.normalMatrix),gt.setValue(R,"modelMatrix",B.matrixWorld),V.isShaderMaterial||V.isRawShaderMaterial){let Ut=V.uniformsGroups;for(let Ht=0,$o=Ut.length;Ht<$o;Ht++){let _i=Ut[Ht];Ge.update(_i,Jt),Ge.bind(_i,Jt)}}return Jt}function Sh(w,O){w.ambientLightColor.needsUpdate=O,w.lightProbe.needsUpdate=O,w.directionalLights.needsUpdate=O,w.directionalLightShadows.needsUpdate=O,w.pointLights.needsUpdate=O,w.pointLightShadows.needsUpdate=O,w.spotLights.needsUpdate=O,w.spotLightShadows.needsUpdate=O,w.rectAreaLights.needsUpdate=O,w.hemisphereLights.needsUpdate=O}function Eh(w){return w.isMeshLambertMaterial||w.isMeshToonMaterial||w.isMeshPhongMaterial||w.isMeshStandardMaterial||w.isShadowMaterial||w.isShaderMaterial&&w.lights===!0}this.getActiveCubeFace=function(){return A},this.getActiveMipmapLevel=function(){return I},this.getRenderTarget=function(){return N},this.setRenderTargetTextures=function(w,O,H){let V=_e.get(w);V.__autoAllocateDepthBuffer=w.resolveDepthBuffer===!1,V.__autoAllocateDepthBuffer===!1&&(V.__useRenderToTexture=!1),_e.get(w.texture).__webglTexture=O,_e.get(w.depthTexture).__webglTexture=V.__autoAllocateDepthBuffer?void 0:H,V.__hasExternalTextures=!0},this.setRenderTargetFramebuffer=function(w,O){let H=_e.get(w);H.__webglFramebuffer=O,H.__useDefaultFramebuffer=O===void 0};let Th=R.createFramebuffer();this.setRenderTarget=function(w,O=0,H=0){N=w,A=O,I=H;let V=!0,B=null,ne=!1,me=!1;if(w){let ve=_e.get(w);if(ve.__useDefaultFramebuffer!==void 0)le.bindFramebuffer(R.FRAMEBUFFER,null),V=!1;else if(ve.__webglFramebuffer===void 0)He.setupRenderTarget(w);else if(ve.__hasExternalTextures)He.rebindTextures(w,_e.get(w.texture).__webglTexture,_e.get(w.depthTexture).__webglTexture);else if(w.depthBuffer){let Ne=w.depthTexture;if(ve.__boundDepthTexture!==Ne){if(Ne!==null&&_e.has(Ne)&&(w.width!==Ne.image.width||w.height!==Ne.image.height))throw new Error("WebGLRenderTarget: Attached DepthTexture is initialized to the incorrect size.");He.setupDepthRenderbuffer(w)}}let Le=w.texture;(Le.isData3DTexture||Le.isDataArrayTexture||Le.isCompressedArrayTexture)&&(me=!0);let Ue=_e.get(w).__webglFramebuffer;w.isWebGLCubeRenderTarget?(Array.isArray(Ue[O])?B=Ue[O][H]:B=Ue[O],ne=!0):w.samples>0&&He.useMultisampledRTT(w)===!1?B=_e.get(w).__webglMultisampledFramebuffer:Array.isArray(Ue)?B=Ue[H]:B=Ue,T.copy(w.viewport),P.copy(w.scissor),U=w.scissorTest}else T.copy(Ae).multiplyScalar(W).floor(),P.copy(fe).multiplyScalar(W).floor(),U=Oe;if(H!==0&&(B=Th),le.bindFramebuffer(R.FRAMEBUFFER,B)&&V&&le.drawBuffers(w,B),le.viewport(T),le.scissor(P),le.setScissorTest(U),ne){let ve=_e.get(w.texture);R.framebufferTexture2D(R.FRAMEBUFFER,R.COLOR_ATTACHMENT0,R.TEXTURE_CUBE_MAP_POSITIVE_X+O,ve.__webglTexture,H)}else if(me){let ve=O;for(let Le=0;Le<w.textures.length;Le++){let Ue=_e.get(w.textures[Le]);R.framebufferTextureLayer(R.FRAMEBUFFER,R.COLOR_ATTACHMENT0+Le,Ue.__webglTexture,H,ve)}}else if(w!==null&&H!==0){let ve=_e.get(w.texture);R.framebufferTexture2D(R.FRAMEBUFFER,R.COLOR_ATTACHMENT0,R.TEXTURE_2D,ve.__webglTexture,H)}v=-1},this.readRenderTargetPixels=function(w,O,H,V,B,ne,me,Ee=0){if(!(w&&w.isWebGLRenderTarget)){console.error("THREE.WebGLRenderer.readRenderTargetPixels: renderTarget is not THREE.WebGLRenderTarget.");return}let ve=_e.get(w).__webglFramebuffer;if(w.isWebGLCubeRenderTarget&&me!==void 0&&(ve=ve[me]),ve){le.bindFramebuffer(R.FRAMEBUFFER,ve);try{let Le=w.textures[Ee],Ue=Le.format,Ne=Le.type;if(!ye.textureFormatReadable(Ue)){console.error("THREE.WebGLRenderer.readRenderTargetPixels: renderTarget is not in RGBA or implementation defined format.");return}if(!ye.textureTypeReadable(Ne)){console.error("THREE.WebGLRenderer.readRenderTargetPixels: renderTarget is not in UnsignedByteType or implementation defined type.");return}O>=0&&O<=w.width-V&&H>=0&&H<=w.height-B&&(w.textures.length>1&&R.readBuffer(R.COLOR_ATTACHMENT0+Ee),R.readPixels(O,H,V,B,Ie.convert(Ue),Ie.convert(Ne),ne))}finally{let Le=N!==null?_e.get(N).__webglFramebuffer:null;le.bindFramebuffer(R.FRAMEBUFFER,Le)}}},this.readRenderTargetPixelsAsync=async function(w,O,H,V,B,ne,me,Ee=0){if(!(w&&w.isWebGLRenderTarget))throw new Error("THREE.WebGLRenderer.readRenderTargetPixels: renderTarget is not THREE.WebGLRenderTarget.");let ve=_e.get(w).__webglFramebuffer;if(w.isWebGLCubeRenderTarget&&me!==void 0&&(ve=ve[me]),ve)if(O>=0&&O<=w.width-V&&H>=0&&H<=w.height-B){le.bindFramebuffer(R.FRAMEBUFFER,ve);let Le=w.textures[Ee],Ue=Le.format,Ne=Le.type;if(!ye.textureFormatReadable(Ue))throw new Error("THREE.WebGLRenderer.readRenderTargetPixelsAsync: renderTarget is not in RGBA or implementation defined format.");if(!ye.textureTypeReadable(Ne))throw new Error("THREE.WebGLRenderer.readRenderTargetPixelsAsync: renderTarget is not in UnsignedByteType or implementation defined type.");let Ze=R.createBuffer();R.bindBuffer(R.PIXEL_PACK_BUFFER,Ze),R.bufferData(R.PIXEL_PACK_BUFFER,ne.byteLength,R.STREAM_READ),w.textures.length>1&&R.readBuffer(R.COLOR_ATTACHMENT0+Ee),R.readPixels(O,H,V,B,Ie.convert(Ue),Ie.convert(Ne),0);let rt=N!==null?_e.get(N).__webglFramebuffer:null;le.bindFramebuffer(R.FRAMEBUFFER,rt);let vt=R.fenceSync(R.SYNC_GPU_COMMANDS_COMPLETE,0);return R.flush(),await iu(R,vt,4),R.bindBuffer(R.PIXEL_PACK_BUFFER,Ze),R.getBufferSubData(R.PIXEL_PACK_BUFFER,0,ne),R.deleteBuffer(Ze),R.deleteSync(vt),ne}else throw new Error("THREE.WebGLRenderer.readRenderTargetPixelsAsync: requested read bounds are out of range.")},this.copyFramebufferToTexture=function(w,O=null,H=0){let V=Math.pow(2,-H),B=Math.floor(w.image.width*V),ne=Math.floor(w.image.height*V),me=O!==null?O.x:0,Ee=O!==null?O.y:0;He.setTexture2D(w,0),R.copyTexSubImage2D(R.TEXTURE_2D,H,0,0,me,Ee,B,ne),le.unbindTexture()};let Ah=R.createFramebuffer(),Ch=R.createFramebuffer();this.copyTextureToTexture=function(w,O,H=null,V=null,B=0,ne=null){ne===null&&(B!==0?(ur("WebGLRenderer: copyTextureToTexture function signature has changed to support src and dst mipmap levels."),ne=B,B=0):ne=0);let me,Ee,ve,Le,Ue,Ne,Ze,rt,vt,lt=w.isCompressedTexture?w.mipmaps[ne]:w.image;if(H!==null)me=H.max.x-H.min.x,Ee=H.max.y-H.min.y,ve=H.isBox3?H.max.z-H.min.z:1,Le=H.min.x,Ue=H.min.y,Ne=H.isBox3?H.min.z:0;else{let ln=Math.pow(2,-B);me=Math.floor(lt.width*ln),Ee=Math.floor(lt.height*ln),w.isDataArrayTexture?ve=lt.depth:w.isData3DTexture?ve=Math.floor(lt.depth*ln):ve=1,Le=0,Ue=0,Ne=0}V!==null?(Ze=V.x,rt=V.y,vt=V.z):(Ze=0,rt=0,vt=0);let st=Ie.convert(O.format),De=Ie.convert(O.type),mt;O.isData3DTexture?(He.setTexture3D(O,0),mt=R.TEXTURE_3D):O.isDataArrayTexture||O.isCompressedArrayTexture?(He.setTexture2DArray(O,0),mt=R.TEXTURE_2D_ARRAY):(He.setTexture2D(O,0),mt=R.TEXTURE_2D),R.pixelStorei(R.UNPACK_FLIP_Y_WEBGL,O.flipY),R.pixelStorei(R.UNPACK_PREMULTIPLY_ALPHA_WEBGL,O.premultiplyAlpha),R.pixelStorei(R.UNPACK_ALIGNMENT,O.unpackAlignment);let je=R.getParameter(R.UNPACK_ROW_LENGTH),Jt=R.getParameter(R.UNPACK_IMAGE_HEIGHT),Wi=R.getParameter(R.UNPACK_SKIP_PIXELS),Kt=R.getParameter(R.UNPACK_SKIP_ROWS),Ir=R.getParameter(R.UNPACK_SKIP_IMAGES);R.pixelStorei(R.UNPACK_ROW_LENGTH,lt.width),R.pixelStorei(R.UNPACK_IMAGE_HEIGHT,lt.height),R.pixelStorei(R.UNPACK_SKIP_PIXELS,Le),R.pixelStorei(R.UNPACK_SKIP_ROWS,Ue),R.pixelStorei(R.UNPACK_SKIP_IMAGES,Ne);let gt=w.isDataArrayTexture||w.isData3DTexture,on=O.isDataArrayTexture||O.isData3DTexture;if(w.isDepthTexture){let ln=_e.get(w),Ut=_e.get(O),Ht=_e.get(ln.__renderTarget),$o=_e.get(Ut.__renderTarget);le.bindFramebuffer(R.READ_FRAMEBUFFER,Ht.__webglFramebuffer),le.bindFramebuffer(R.DRAW_FRAMEBUFFER,$o.__webglFramebuffer);for(let _i=0;_i<ve;_i++)gt&&(R.framebufferTextureLayer(R.READ_FRAMEBUFFER,R.COLOR_ATTACHMENT0,_e.get(w).__webglTexture,B,Ne+_i),R.framebufferTextureLayer(R.DRAW_FRAMEBUFFER,R.COLOR_ATTACHMENT0,_e.get(O).__webglTexture,ne,vt+_i)),R.blitFramebuffer(Le,Ue,me,Ee,Ze,rt,me,Ee,R.DEPTH_BUFFER_BIT,R.NEAREST);le.bindFramebuffer(R.READ_FRAMEBUFFER,null),le.bindFramebuffer(R.DRAW_FRAMEBUFFER,null)}else if(B!==0||w.isRenderTargetTexture||_e.has(w)){let ln=_e.get(w),Ut=_e.get(O);le.bindFramebuffer(R.READ_FRAMEBUFFER,Ah),le.bindFramebuffer(R.DRAW_FRAMEBUFFER,Ch);for(let Ht=0;Ht<ve;Ht++)gt?R.framebufferTextureLayer(R.READ_FRAMEBUFFER,R.COLOR_ATTACHMENT0,ln.__webglTexture,B,Ne+Ht):R.framebufferTexture2D(R.READ_FRAMEBUFFER,R.COLOR_ATTACHMENT0,R.TEXTURE_2D,ln.__webglTexture,B),on?R.framebufferTextureLayer(R.DRAW_FRAMEBUFFER,R.COLOR_ATTACHMENT0,Ut.__webglTexture,ne,vt+Ht):R.framebufferTexture2D(R.DRAW_FRAMEBUFFER,R.COLOR_ATTACHMENT0,R.TEXTURE_2D,Ut.__webglTexture,ne),B!==0?R.blitFramebuffer(Le,Ue,me,Ee,Ze,rt,me,Ee,R.COLOR_BUFFER_BIT,R.NEAREST):on?R.copyTexSubImage3D(mt,ne,Ze,rt,vt+Ht,Le,Ue,me,Ee):R.copyTexSubImage2D(mt,ne,Ze,rt,Le,Ue,me,Ee);le.bindFramebuffer(R.READ_FRAMEBUFFER,null),le.bindFramebuffer(R.DRAW_FRAMEBUFFER,null)}else on?w.isDataTexture||w.isData3DTexture?R.texSubImage3D(mt,ne,Ze,rt,vt,me,Ee,ve,st,De,lt.data):O.isCompressedArrayTexture?R.compressedTexSubImage3D(mt,ne,Ze,rt,vt,me,Ee,ve,st,lt.data):R.texSubImage3D(mt,ne,Ze,rt,vt,me,Ee,ve,st,De,lt):w.isDataTexture?R.texSubImage2D(R.TEXTURE_2D,ne,Ze,rt,me,Ee,st,De,lt.data):w.isCompressedTexture?R.compressedTexSubImage2D(R.TEXTURE_2D,ne,Ze,rt,lt.width,lt.height,st,lt.data):R.texSubImage2D(R.TEXTURE_2D,ne,Ze,rt,me,Ee,st,De,lt);R.pixelStorei(R.UNPACK_ROW_LENGTH,je),R.pixelStorei(R.UNPACK_IMAGE_HEIGHT,Jt),R.pixelStorei(R.UNPACK_SKIP_PIXELS,Wi),R.pixelStorei(R.UNPACK_SKIP_ROWS,Kt),R.pixelStorei(R.UNPACK_SKIP_IMAGES,Ir),ne===0&&O.generateMipmaps&&R.generateMipmap(mt),le.unbindTexture()},this.initRenderTarget=function(w){_e.get(w).__webglFramebuffer===void 0&&He.setupRenderTarget(w)},this.initTexture=function(w){w.isCubeTexture?He.setTextureCube(w,0):w.isData3DTexture?He.setTexture3D(w,0):w.isDataArrayTexture||w.isCompressedArrayTexture?He.setTexture2DArray(w,0):He.setTexture2D(w,0),le.unbindTexture()},this.resetState=function(){A=0,I=0,N=null,le.reset(),he.reset()},typeof __THREE_DEVTOOLS__<"u"&&__THREE_DEVTOOLS__.dispatchEvent(new CustomEvent("observe",{detail:this}))}get coordinateSystem(){return vn}get outputColorSpace(){return this._outputColorSpace}set outputColorSpace(e){this._outputColorSpace=e;let t=this.getContext();t.drawingBufferColorSpace=Ke._getDrawingBufferColorSpace(e),t.unpackColorSpace=Ke._getUnpackColorSpace()}};var Q=i=>document.getElementById(i),wc=Object.create(null),Q0={camera:5,yolo:5,midas:5,odometry:5,segmentation:5,radar:2,gps:5,imu:2,tof:2},Uu=["camera","radar","gps","imu","tof","lidar","ultrasonic"],ws={horizontalFovDeg:70,yawOffsetDeg:0,lateralOffsetM:0,calibrated:!1},hc=.25,ex=1.25,tx=8,Do=.5,nx=5;function At(i,e,t,n){wc[e]=t;let r=Q(i);if(r){r.dataset.state=t;let c=t==="live"?"LIVE":t==="stale"?"STALE":t==="offline"?"OFFLINE":"LOADING";r.textContent=n.toUpperCase().startsWith(`${c} \xB7`)?n:`${c} \xB7 ${n}`}let s=e==="tof"?r?.closest(".sensor-readout-card"):null;if(s){let c=document.querySelector('.world-map-offline-pill[data-source="tof"]');if(s.hidden=t!=="live",c){c.hidden=t==="live";let l=c.querySelector("[data-offline-reason]");l&&(l.textContent=n)}}let a=Uu.filter(c=>wc[c]==="live").length,o=Q("world-map-summary-live");o&&(o.textContent=`${a} / ${Uu.length}`)}var jn=(i,e,t)=>t?Number.isFinite(e)&&e>Q0[i]?"stale":"live":"offline",fc=new Set;function Lo(i,e){e?fc.add(i):fc.delete(i);let t=Q("world-map-cloud-fetch");t&&(t.hidden=fc.size===0)}var Zt=null,Mc=0,pc=!1,gi=null,Ss=null,Rr=null,kt=null,mc="",Ou=null,Bu="",zu="",Ui=[],ix=1,ut=null,gc=0,Io="",Sc="",Yt=null,Ar=!1,an="",Fo="",Po=null,Zn=[],ku="",fn=null,En=null,Tr=[],_t=0,Oi=[],Qu=0,vs=[];function rx(i,e=.2){let t=Number(i);if(!Number.isFinite(t))return null;let n=Oi.filter(c=>c.attitude_valid&&Number.isFinite(Number(c.timestamp))&&Number.isFinite(Number(c.roll_deg))&&Number.isFinite(Number(c.pitch_deg)));if(!n.length)return null;let r=null,s=null;for(let c of n){let l=Number(c.timestamp);l<=t&&(!r||l>Number(r.timestamp))&&(r=c),l>=t&&(!s||l<Number(s.timestamp))&&(s=c)}let a=(c,l)=>(l-c+540)%360-180;if(r&&s&&Number(s.timestamp)-Number(r.timestamp)<=.25){let c=Number(s.timestamp)-Number(r.timestamp),l=c>0?(t-Number(r.timestamp))/c:0,u=d=>Number(r[d])+a(Number(r[d]),Number(s[d]))*l;return{roll_deg:u("roll_deg"),pitch_deg:u("pitch_deg"),timestamp:t}}let o=n.reduce((c,l)=>!c||Math.abs(Number(l.timestamp)-t)<Math.abs(Number(c.timestamp)-t)?l:c,null);return Math.abs(Number(o.timestamp)-t)<=e?o:null}function Ic(i){let e=rx(i);return e?new Gt().setFromEuler(new en(bt.degToRad(Number(e.roll_deg)),bt.degToRad(Number(e.pitch_deg)),0,"XYZ")):null}function sx(i,e=.1){let t=Number(i);return Tr.reduce((n,r)=>{let s=Math.abs(Number(r.timestamp)-t);return s<=e&&(!n||s<n.age)?{sample:r,age:s}:n},null)?.sample||null}var pn=document.querySelector("#view-worldmodel .map-panel");if(pn){let i=pn.querySelector(".panel-head"),e=pn.querySelector(".map-layout"),t=pn.querySelector(".map-wrap"),n=pn.querySelector(".map-intro");if(i&&e&&t&&!Q("world-map-source")){let r=document.createElement("div");r.className="world-map-controls",r.innerHTML='<div class="world-map-segment" role="group" aria-label="Map rendering"><button type="button" data-render="2d" aria-pressed="true">2D</button><button type="button" data-render="3d" aria-pressed="false">3D</button></div><small id="world-map-state" role="status">Simulation \xB7 2D</small>',i.append(r);let s=document.createElement("div");s.id="world-map-sim-3d",s.className="world-map-canvas",s.hidden=!0,e.insertBefore(s,t);let a=document.createElement("section");a.id="world-map-sensor-view",a.className="world-map-sensor-view",a.hidden=!0,a.innerHTML='<div class="world-map-sensor-metrics"><span>Camera <b id="world-map-camera-state">Waiting</b></span><span>YOLOX <b id="world-map-yolo-state">Waiting</b></span><span>MiDaS <b id="world-map-midas-state">Waiting</b></span><span>Visual odometry <b id="world-map-odometry-state">Waiting</b></span><span>SegFormer <b id="world-map-segmentation-state">disabled</b></span><span>Frame <b id="world-map-frame-state">\u2014</b></span></div><div id="world-map-sensor-2d" class="world-map-sensor-2d"><div class="world-map-camera"><div class="world-map-sensor-heading">CAMERA \xB7 YOLOX</div><div class="world-map-image-wrap"><img id="world-map-camera-image" alt="Live camera frame with YOLOX detections"><svg id="world-map-yolo-overlay" viewBox="0 0 1 1" preserveAspectRatio="xMidYMid meet" aria-hidden="true"></svg><span id="world-map-camera-empty" class="world-map-empty">Waiting for a camera frame</span></div></div><div class="world-map-depth"><div class="world-map-sensor-heading">MiDaS \xB7 RELATIVE DEPTH</div><img id="world-map-depth-image" alt="MiDaS relative depth image"><span id="world-map-depth-empty" class="world-map-empty">MiDaS disabled or waiting for inference</span><div class="world-map-depth-calibration"><button type="button" id="world-map-midas-calibrate">Start calibration</button><button type="button" data-calibration-log-download>Download calibration log</button><a href="/body/camera/depth-calibration/log" target="_blank" rel="noopener">Open log</a><small id="world-map-midas-calibration-status" role="status">Relative depth only \xB7 not calibrated in metres</small></div></div></div><section class="world-map-odometry-view" aria-label="Experimental visual odometry trajectory"><div class="world-map-sensor-heading"><span>VISUAL ODOMETRY \xB7 LOCAL TRAJECTORY</span><small id="world-map-odometry-map-status">Waiting for tracking</small></div><div class="odom-plot"><canvas id="world-map-odometry-map" role="img" aria-label="Top-down estimated Body trajectory in the local visual odometry frame"></canvas><span class="odom-edge-label odom-forward">FORWARD \u2191</span><span class="odom-edge-label odom-lateral">\u2190 LEFT \xB7 RIGHT \u2192</span><span id="world-map-odometry-position" class="odom-position-label">0.00, 0.00 m</span></div><p class="world-map-odometry-footnote">Session-local estimate \xB7 drift accumulates \xB7 not a persistent map</p></section><section class="world-map-segmentation-panel" aria-label="SegFormer semantic segmentation"><div class="world-map-sensor-heading"><span>SEGFORMER \xB7 SEMANTIC MASK</span><small>Independent of camera preview</small></div><div class="world-map-segmentation-preview"><canvas id="world-map-segmentation-overlay" aria-label="Standalone SegFormer semantic class mask" hidden></canvas><span id="world-map-segmentation-empty" class="world-map-empty">Waiting for a SegFormer mask</span></div><div id="world-map-segmentation-classes" class="world-map-segmentation-classes">Waiting for SegFormer classes</div></section><div id="world-map-sensor-3d" class="world-map-sensor-cloud-layout" hidden><div id="world-map-sensor-3d-viewport" class="world-map-canvas world-map-sensor-cloud"><div class="world-map-cloud-hud"><span id="world-map-cloud-hud-points">0 points</span><span id="world-map-cloud-hud-depth">MiDaS \u2014</span><span id="world-map-cloud-hud-age">Frame \u2014</span><span id="world-map-cloud-hud-sync">Camera/depth \u2014</span><span id="world-map-cloud-hud-pipeline">Pipeline \u2014</span><span id="world-map-cloud-hud-fps">3D \u2014 FPS</span><div class="world-map-cloud-stale" id="world-map-cloud-stale" hidden role="status"></div></div><div class="world-map-cloud-controls"><button type="button" data-cloud-action="reset" title="Reset camera to fit point cloud">Reset</button><button type="button" data-cloud-view="camera" title="Pinhole camera view; FOV is estimated unless intrinsics are provided">Camera</button><button type="button" data-cloud-view="top">Top</button><button type="button" data-cloud-view="side">Side</button><button type="button" data-cloud-view="follow">Follow</button><label>Point size <input id="world-map-cloud-point-size" type="range" min="10" max="50" value="25" aria-label="3D point size"></label></div><div class="world-map-cloud-labels" aria-hidden="true"></div><div class="world-map-cloud-scale" hidden>1 m</div><div id="world-map-cloud-fetch" class="world-map-cloud-fetch" hidden>Sensor data unavailable: fetch failed, retrying</div></div><aside class="world-map-cloud-side"><strong>Scene layers</strong><label><input type="checkbox" data-cloud-layer="cloud" checked> MiDaS point cloud</label><label><input type="checkbox" data-cloud-layer="detections" checked> YOLOX detections</label><label><input type="checkbox" data-cloud-layer="radar" checked> mmWave targets (metres)</label><label><input type="checkbox" data-cloud-layer="odometry" checked> Odometry trail</label><strong>Depth units</strong><div class="world-map-depth-legend"><i></i><div><span>Near</span><span>Far</span></div></div><small id="world-map-cloud-depth-caption">Relative units \xB7 not metric</small><small>Radar markers use metres, independently scaled from an uncalibrated MiDaS cloud.</small><div class="world-map-depth-calibration"><button type="button" id="world-map-midas-calibrate-3d">Start calibration</button><button type="button" data-calibration-log-download>Download calibration log</button><a href="/body/camera/depth-calibration/log" target="_blank" rel="noopener">Open log</a><small id="world-map-midas-calibration-status-3d" role="status">Relative depth only \xB7 not calibrated in metres</small></div><div class="world-map-cloud-axis" aria-label="XYZ orientation: X right, Y up, Z forward"><span>X \u2192</span><span>Y \u2191</span><span>Z \u2299</span></div></aside></div><p id="world-map-sensor-note" class="world-map-sensor-note">Sensor-only view \xB7 no simulation object positions are used.</p>',a.querySelector('[data-cloud-layer="radar"]').checked=!0,a.querySelector("#world-map-cloud-hud-fps").textContent="3D \u2014 FPS";for(let T of["world-map-camera-state","world-map-yolo-state","world-map-midas-state","world-map-odometry-state","world-map-segmentation-state","world-map-radar-state","world-map-gps-state","world-map-imu-state","world-map-tof-state"]){let P=Q(T);P&&(P.dataset.state="loading")}let o=document.createElement("section");o.id="world-map-live-readouts",o.className="world-map-live-readouts",o.innerHTML='<article class="sensor-readout-card"><header><strong>mmWave \xB7 LD2450</strong><small id="world-map-radar-state">Waiting</small></header><canvas id="world-map-radar-plot" height="190" aria-label="Live mmWave target positions and radial velocities"></canvas><div id="world-map-radar-targets" class="sensor-target-list">Waiting for radar data.</div></article><article class="sensor-readout-card"><header><strong>GPS / GNSS \xB7 D0/D1</strong><small id="world-map-gps-state">Waiting</small></header><div class="sensor-readout-values"><span>Position<b id="world-map-gps-position">No fix</b></span><span>Fix / quality<b id="world-map-gps-fix">\u2014</b></span><span>Satellites<b id="world-map-gps-satellites">\u2014 used \xB7 \u2014 in view</b></span><span>HDOP / altitude<b id="world-map-gps-quality">\u2014</b></span></div><div id="world-map-gps-signals" class="sensor-gps-signals" role="img" aria-label="GPS satellite signal strength by satellite"></div></article><article class="sensor-readout-card"><header><strong>Modulino Movement \xB7 IMU</strong><small id="world-map-imu-state">Waiting</small></header><div id="world-map-imu-attitude" class="imu-attitude" role="img" aria-label="IMU attitude indicator based on roll and pitch"><div class="imu-attitude-disc" aria-hidden="true"><div class="imu-attitude-horizon"><span></span></div><i class="imu-attitude-mark"></i></div><div><b>ATTITUDE</b><small>Roll / pitch \xB7 no magnetic heading</small></div></div><div class="sensor-readout-values"><span>Roll<b id="world-map-imu-roll">\u2014</b></span><span>Pitch<b id="world-map-imu-pitch">\u2014</b></span><span>Yaw rate<b id="world-map-imu-yaw">\u2014</b></span><span>Acceleration \xB7 g<b id="world-map-imu-accel">\u2014</b></span><span>Angular rate \xB7 \xB0/s<b id="world-map-imu-gyro">\u2014</b></span></div><p class="sensor-readout-note">Six-axis IMU; yaw is relative angular rate, not a magnetic heading.</p></article><article class="sensor-readout-card"><header><strong>ToF \xB7 VL53L1X</strong><small id="world-map-tof-state">Waiting</small></header><div class="sensor-distance"><b id="world-map-tof-distance">\u2014</b><span id="world-map-tof-meta">Forward single-beam range</span></div></article><article class="sensor-readout-card"><header><strong>LiDAR</strong><small id="world-map-lidar-state">No live source</small></header><p class="sensor-readout-note">No physical LiDAR stream is connected to this Body view. Any LiDAR volume shown in Simulation is virtual and is kept out of this live sensor view.</p></article><article class="sensor-readout-card"><header><strong>Ultrasonic \xB7 HC-SR04</strong><small id="world-map-ultrasonic-state">No live source</small></header><div class="sensor-readout-values sensor-range-channels"><span>Front-left<b id="world-map-ultrasonic-left">No data</b></span><span>Front-right<b id="world-map-ultrasonic-right">No data</b></span><span>Rear<b id="world-map-ultrasonic-rear">No data</b></span></div><p class="sensor-readout-note">Waiting for the ultrasonic firmware/gateway data channel; no simulated ranges are shown here.</p></article>';let c=(T,P)=>{let U=o.querySelector(`#${T}`),F=U?.closest("header"),k=F?.querySelector("strong");if(!U||!F||!k)return;let G=document.createElement("div");G.className="sensor-heading-copy",k.title=P;let K=document.createElement("span");K.className="sensor-card-source",K.textContent=P,K.title=P,G.append(k,K),U.classList.add("sensor-state-chip"),F.replaceChildren(G,U)};c("world-map-radar-state","hlk_ld2450_ventuno_bridge"),c("world-map-gps-state","Serial1 USART3 \xB7 D0/D1 via Ventuno STM32 Bridge"),c("world-map-imu-state","Arduino Modulino Movement / LSM6DSOX");let l=document.createElement("article");l.id="world-map-compute-power",l.className="sensor-readout-card world-map-compute-card",l.innerHTML='<header><strong>Compute & power</strong><small id="world-map-system-state">Sampling</small></header><div class="system-instrument-grid"><article class="system-instrument"><span class="system-instrument-label">CPU LOAD</span><div class="system-gauge" id="world-map-cpu-gauge" role="img" aria-label="CPU utilization"><div class="system-gauge-center"><strong id="world-map-system-cpu-value">\u2014</strong><small>%</small></div></div><span class="system-instrument-foot" id="world-map-system-cpu-temp">CPU temp \xB7 \u2014</span></article><article class="system-instrument"><span class="system-instrument-label">CPU TEMP</span><div class="system-gauge system-gauge-temp" id="world-map-cpu-temp-gauge" role="img" aria-label="Maximum CPU temperature"><div class="system-gauge-center"><strong id="world-map-system-cpu-temp-value">\u2014</strong><small>\xB0C</small></div></div><span class="system-instrument-foot">Hottest reported CPU sensor \xB7 0\u2013100 \xB0C</span></article><article class="system-instrument"><span class="system-instrument-label">GPU TEMP</span><div class="system-gauge system-gauge-temp" id="world-map-gpu-temp-gauge" role="img" aria-label="Maximum GPU temperature"><div class="system-gauge-center"><strong id="world-map-system-gpu-temp-value">\u2014</strong><small>\xB0C</small></div></div><span class="system-instrument-foot" id="world-map-system-gpu-meta">Load unavailable \xB7 \u2014 MHz</span></article><article class="system-instrument"><span class="system-instrument-label">MEMORY</span><div class="system-gauge" id="world-map-memory-gauge" role="img" aria-label="Memory utilization"><div class="system-gauge-center"><strong id="world-map-system-memory-value">\u2014</strong><small>%</small></div></div><span class="system-instrument-foot" id="world-map-system-memory-meta">\u2014 free</span></article><article class="system-instrument"><span class="system-instrument-label">BOARD INPUT</span><div class="system-gauge system-gauge-power" id="world-map-power-gauge" role="img" aria-label="Measured board input power"><div class="system-gauge-center"><strong id="world-map-system-power-value">\u2014</strong><small>W</small></div></div><span class="system-instrument-foot" id="world-map-system-power-meta">INA232 \xB7 measured rail</span></article></div><div class="system-telemetry-strip"><div><span>GPU utilization</span><strong id="world-map-system-gpu-load">Unavailable</strong></div><div><span>GPU clock</span><strong id="world-map-system-gpu-clock">\u2014</strong></div><div><span>Qualcomm HTP</span><strong id="world-map-system-htp">Waiting for inference status</strong></div><div><span>Energy since Body start</span><strong id="world-map-system-energy">\u2014</strong></div></div><p id="world-map-system-note" class="sensor-readout-note">GPU/HTP usage percentages require kernel counters. Board input may exclude external motor loads.</p>',a.append(o,l);let u=a.querySelector(".world-map-sensor-2d"),d=a.querySelector(".world-map-odometry-view"),h=a.querySelector(".world-map-segmentation-panel"),p=Q("world-map-odometry-map");p&&typeof ResizeObserver<"u"&&new ResizeObserver(()=>yh()).observe(p.parentElement);let g=document.createElement("div");g.className="world-map-vision-footer",g.append(a.querySelector("#world-map-sensor-note")),u?.after(g),o.querySelector("#world-map-radar-state")?.closest(".sensor-readout-card")?.classList.remove("sensor-readout-wide"),d&&u?.append(d),h&&u?.append(h);let m=document.createElement("div");m.className="world-map-status-bar",m.setAttribute("aria-label","Live Body and sensor status"),m.innerHTML='<span>BODY <b id="world-map-body-status" data-state="loading">Connecting</b></span><span>BOARD INPUT <b id="world-map-summary-power">\u2014 W</b></span><span>ENERGY <b id="world-map-summary-energy">\u2014 Wh</b></span><span>LATEST FRAME <b id="world-map-summary-frame">\u2014</b></span><span>SENSORS LIVE <b id="world-map-summary-live">0 / 7</b></span>',m.append(a.querySelector("#world-map-cloud-fetch"),a.querySelector(".world-map-sensor-metrics")),a.prepend(m);let f=document.querySelector("#message"),S=()=>{let T=f?.textContent?.trim()||"",P=/connected/i.test(T)&&!/disconnected|not connected/i.test(T),U=Q("world-map-body-status");U&&(U.textContent=T||"Status unavailable",U.dataset.state=P?"live":T?"offline":"loading")};f&&new MutationObserver(S).observe(f,{childList:!0,characterData:!0,subtree:!0}),S();let M=document.createElement("div");M.className="world-map-offline-strip",M.setAttribute("aria-label","Offline sensors"),M.innerHTML="<strong>OFFLINE</strong>";let y=(T,P,U)=>{let F=o.querySelector(`#${T}`),k=document.createElement("span");return k.className="world-map-offline-pill",k.title=U,k.innerHTML=`<b>${P}</b> <span>${U}</span>`,F&&(F.dataset.offlinePill="true",k.prepend(F),F.dataset.state="offline",F.textContent="OFFLINE"),wc[P==="LiDAR"?"lidar":"ultrasonic"]="offline",M.append(k),k},C=o.querySelector("#world-map-lidar-state")?.closest(".sensor-readout-card"),A=o.querySelector("#world-map-ultrasonic-state")?.closest(".sensor-readout-card");y("world-map-lidar-state","LiDAR","No physical stream connected"),y("world-map-ultrasonic-state","HC-SR04","Waiting for firmware/gateway channel");let I=document.createElement("span");I.className="world-map-offline-pill",I.dataset.source="tof",I.innerHTML="<b>ToF \xB7 VL53L1X</b> <span data-offline-reason>Sensor not detected</span>",M.append(I);let N=o.querySelector("#world-map-tof-state")?.closest(".sensor-readout-card");N&&(N.hidden=!0,N.dataset.source="tof"),C?.remove(),A?.remove();let v=o.querySelector("#world-map-tof-state")?.closest(".sensor-readout-card");v&&(v.hidden=!0),a.append(M),a.querySelector(".world-map-segmentation-panel .world-map-sensor-heading small")?.remove(),e.after(a);let b=document.createElement("style");b.textContent=`
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
      .world-map-depth-calibration button,.world-map-depth-calibration a{border:1px solid #416b54;border-radius:3px;background:#10251a;color:#d9f5e5;padding:7px 10px;cursor:pointer;text-decoration:none}
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
      .world-map-cloud-side .world-map-depth-calibration button,.world-map-cloud-side .world-map-depth-calibration a{justify-self:start;padding:8px 10px;border:1px solid #126d76;border-radius:6px;background:#102b36;color:#bdf9f3;cursor:pointer;text-decoration:none;font:12px ui-sans-serif,system-ui,sans-serif}
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
    `,document.head.append(b)}}var No=(i,e=1)=>new rs({color:i,roughness:.82,metalness:.02,transparent:e<1,opacity:e}),Hu={target:"#efa678",chair:"#83b3d5",table:"#d3bd67",obstacle:"#a77ba5",mobile_obstacle:"#db83bf",object:"#a9c4b2"};function eh(i,e="#07120f"){if(!i)return null;let t;try{t=new Co({antialias:!0,alpha:!1,powerPreference:"low-power"})}catch(u){return i.textContent=`3D rendering unavailable: ${u.message}`,null}t.setPixelRatio(Math.min(window.devicePixelRatio||1,1.5)),t.setClearColor(e,1),i.prepend(t.domElement);let n=new Jr;n.background=new Be(e);let r=new Dt(42,1,.05,200);n.add(new os("#d7f4e4","#14231c",2));let s=new cs("#e4fff0",2.2);s.position.set(-4,10,6),n.add(s);let a=()=>{let u=Math.max(1,i.clientWidth),d=Math.max(1,i.clientHeight);t.setSize(u,d,!1),r.aspect=u/d,r.updateProjectionMatrix()},o=new ResizeObserver(a);o.observe(i),a();let c=null;i.addEventListener("contextmenu",u=>u.preventDefault()),i.addEventListener("pointerdown",u=>{c={x:u.clientX,y:u.clientY,pan:u.button===2||u.shiftKey},r.userData.userAdjusted=!0,i.setPointerCapture(u.pointerId)}),i.addEventListener("pointermove",u=>{if(!c)return;let d=u.clientX-c.x,h=u.clientY-c.y;c.x=u.clientX,c.y=u.clientY;let p=r.userData.target||new D;if(c.pan){let g=r.position.distanceTo(p)*.0018,x=new D().setFromMatrixColumn(r.matrix,0),m=new D().setFromMatrixColumn(r.matrix,1),f=x.multiplyScalar(-d*g).add(m.multiplyScalar(h*g));r.position.add(f),p.add(f),r.userData.target=p}else{let g=new ds().setFromVector3(r.position.clone().sub(p));g.theta-=d*.006,g.phi=bt.clamp(g.phi+h*.006,.12,Math.PI-.12),r.position.copy(new D().setFromSpherical(g).add(p))}r.lookAt(p),l()}),i.addEventListener("pointerup",()=>{c=null}),i.addEventListener("pointercancel",()=>{c=null}),i.addEventListener("wheel",u=>{u.preventDefault(),r.userData.userAdjusted=!0;let d=r.userData.target||new D,h=r.position.clone().sub(d);h.multiplyScalar(bt.clamp(1+u.deltaY*.001,.82,1.2)),r.position.copy(d).add(h),l()},{passive:!1});let l=()=>t.render(n,r);return{renderer:t,scene:n,camera:r,render:l,resize:a,observer:o}}var Ln=eh(Q("world-map-sim-3d")),sn,Vu="",xe=eh(Q("world-map-sensor-3d-viewport"),"#05070d"),at=null,mi=null,Gu="",Cr="",Ec=!1,Xt=null,Tc=0,th="",Wu="",Bi=new Bt,zi=new Bt,Uo=null,Oo=null,Xu="",bs=new Bt,Ms=new Bt;if(xe){let i=[],e=[];for(let s=-10;s<=10;s+=1){let a=new Be(s%5===0?"#426078":"#23394a");i.push(s,0,1,s,0,-15,-10,0,-4+s,10,0,-4+s);for(let o=0;o<4;o+=1)e.push(a.r,a.g,a.b)}let t=new ft;t.setAttribute("position",new nt(i,3)),t.setAttribute("color",new nt(e,3)),Bi.add(new ci(t,new nn({vertexColors:!0,transparent:!0,opacity:.78}))),Uo=new Xn(new ft().setFromPoints([new D(0,0,0),new D(0,.18,0)]),new nn({color:"#9aafc0",transparent:!0,opacity:.8})),Bi.add(Uo),Oo=new dt(new di(.022,12,8),new Wt({color:"#62f1c1"})),Bi.add(Oo),zi.add(new dt(new di(.025,16,10),new Wt({color:"#f4f7ff"})));let n=(s,a)=>{let o=new D(...s).normalize();zi.add(new hs(o,new D,.2,a,.045,.028))};n([1,0,0],"#ef6a73"),n([0,1,0],"#62d994"),n([0,0,-1],"#66a8ff");let r=new ft().setFromPoints([new D(-.5,.03,-2),new D(.5,.03,-2)]);Bi.add(new Xn(r,new nn({color:"#d7eaf4"}))),xe.scene.add(Bi,zi,bs,Ms)}var yt=Q("world-map-sensor-3d-viewport");yt?.querySelector(".world-map-cloud-axis span:last-child")?.replaceChildren("Z\u2212 \xB7 forward");var Bo=yt?.querySelector(".world-map-cloud-labels"),Ac=0,$u=performance.now();if(xe){let i=xe.render,e=0;xe.render=()=>{i(),Ac+=1,vh();let t=performance.now();t-e>=500&&(Kn(),e=t)},yt?.querySelector('[data-cloud-action="reset"]')?.addEventListener("click",()=>{yt.classList.remove("is-camera-view"),xe.camera.fov=42,xe.camera.userData.userAdjusted=!1,Ec=!1,xe.resize(),Kn(),Hi(),Es(),Go()}),yt?.querySelectorAll("[data-cloud-view]").forEach(t=>t.addEventListener("click",()=>Rx(t.dataset.cloudView))),yt?.querySelectorAll("[data-cloud-layer]").forEach(t=>t.addEventListener("change",()=>{let n=t.dataset.cloudLayer;n==="cloud"&&at&&(at.visible=t.checked),n==="detections"&&(mi&&(mi.visible=t.checked),t.checked&&ut&&Wo(ut,Ss)),n==="radar"&&Hi(En,!0),n==="odometry"&&(Ms.visible=t.checked),xe.render()})),Q("world-map-cloud-point-size")?.addEventListener("input",t=>{at&&(at.material.uniforms.uPointSize.value=Number(t.target.value)/1e3),xe.render()})}var qu=0;function nh(i){document.visibilityState!=="hidden"&&pt==="sensors"&&Rt==="3d"&&xe&&i-qu>=1e3/24&&(qu=i,xe.render()),requestAnimationFrame(nh)}requestAnimationFrame(nh);var pt=window.bodyWorldModelView==="sensors"?"sensors":"simulation",Rt="2d",ki=null,xc=!1,_c=!1;function ax(i,e,t){let n=new dt(new Ai(e,t),No("#0d1b15"));n.rotation.x=-Math.PI/2,n.position.y=-.03,i.add(n);let r=new us(Math.max(e,t),Math.ceil(Math.max(e,t)*2),"#4e8d69","#294c3a");r.position.y=.005,i.add(r);let s=new ci(new is(new Mn(e,.08,t)),new nn({color:"#70b28a",transparent:!0,opacity:.72}));s.position.y=.01,i.add(s)}function ox(i){let e=String(i.kind||"object").toLowerCase(),t=Math.max(.25,Math.min(2.2,Number(i.size)||.6));return e.includes("chair")?new Mn(t*1.15,.8,t*1.05):e.includes("table")?new Mn(t*1.6,.72,t*1.4):e.includes("obstacle")?new In(t*.52,t*.62,1.15,18):e==="target"||e.includes("cup")?new In(t*.34,t*.42,.48,18):new Mn(t,Math.max(.35,t),t)}function yc(i,e="#d8eee1"){let t=document.createElement("canvas");t.width=512,t.height=96;let n=t.getContext("2d");n.font="600 42px ui-monospace, monospace",n.textAlign="center",n.textBaseline="middle",n.fillStyle="#06100de8",n.fillRect(0,10,t.width,t.height-20),n.fillStyle=e,n.fillText(String(i).slice(0,32),t.width/2,t.height/2);let r=new es(t);r.colorSpace=Nt;let s=new jr(new mr({map:r,transparent:!0,depthTest:!1}));return s.scale.set(1.65,.31,1),s}function Ho(i){if(!Ln)return;let e=i?.perception||{},t=i?.sim||{},n=i?.mode==="sim",r=Object.entries(t.objects||{}).map(([y,C])=>({id:y,label:y.replaceAll("_"," "),kind:C.kind,position:[C.x,C.y,0],size:y==="cup"?.4:.8})),s=n?r:Array.isArray(e.objects)?e.objects:r,a=n?t.body||[0,0,0]:e.body?.position||t.body||[0,0,0],o=Math.max(2,Number(t.width)||12),c=Math.max(2,Number(t.height)||12),l=t.shelf||[1,9],u=n?Number(t.heading_deg||0)*Math.PI/180:Number(e.body?.orientation||0),d=JSON.stringify([o,c,l,a,u,s.map(y=>[y.id,y.kind,y.position,y.size])]);if(d===Vu)return;Vu=d,sn&&(Ln.scene.remove(sn),sn.traverse(y=>{y.geometry?.dispose(),Array.isArray(y.material)?y.material.forEach(C=>C.dispose()):y.material?.dispose()})),sn=new Bt,ax(sn,o,c);let h=new dt(new In(.48,.48,.035,32),new Wt({color:"#79d8a0",transparent:!0,opacity:.32}));h.position.set(Number(l[0])-o/2,.02,-(Number(l[1])-c/2)),sn.add(h);let p=yc("GOAL","#b9f5ce");p.position.set(h.position.x,.35,h.position.z),sn.add(p);let g=new Bt;g.position.set(Number(a[0])-o/2,0,-(Number(a[1])-c/2));let x=new dt(new In(.28,.32,.32,24),No("#8ee5b1"));x.position.y=.2,g.add(x);let m=new dt(new xr(.13,.38,16),No("#d8ffe5"));m.rotation.z=-Math.PI/2,m.position.set(.38,.24,0),g.add(m),g.rotation.y=-u,sn.add(g);let f=yc("BODY","#b6f1d3");f.position.set(g.position.x,.82,g.position.z),sn.add(f);for(let y of s){let C=y.position||[0,0,0],A=String(y.kind||"object").toLowerCase(),I=Hu[A]||Hu.object,N=new dt(ox(y),No(I,A.includes("mobile")?.92:1)),v=A.includes("obstacle")?.58:A==="table"||A==="chair"?.38:.25;N.position.set(Number(C[0])-o/2,v,-(Number(C[1])-c/2)),sn.add(N);let b=new dt(new In(.025,.025,.025,10),new Wt({color:I}));b.position.set(N.position.x,.035,N.position.z),sn.add(b);let T=yc(y.label||y.kind||"OBJECT",I);T.position.set(N.position.x,v+.86,N.position.z),sn.add(T)}Ln.scene.add(sn);let S=new D(0,0,0);Ln.camera.userData.target=S;let M=Math.max(o,c)*1.3;Ln.camera.userData.userAdjusted||(Ln.camera.position.set(0,M*.62,M),Ln.camera.lookAt(S)),Ln.render()}function ih(i){pt=i;let e=Q("world-map-sensor-view"),t=pn?.querySelector(".map-layout");e&&(e.hidden=i!=="sensors"),t&&(t.hidden=i==="sensors");let n=pn?.querySelector('.panel-head button[onclick="expandMap()"]');n&&(n.hidden=i==="sensors");let r=pn?.querySelector(".panel-head h2");r&&(r.textContent=i==="sensors"?"Live sensor observatory":"Simulation \xB7 world ground truth"),pn?.querySelector(".map-intro")?.replaceChildren(document.createTextNode(i==="sensors"?"Live hardware and perception feeds only. No simulator positions, virtual LiDAR returns or synthetic objects are included.":"Synthetic room, robot pose and object positions for controlled testing. These are simulation ground truth, not live sensor measurements.")),pn?.querySelector(".truth-note")?.toggleAttribute("hidden",i==="sensors"),document.querySelectorAll(".simulation-actions").forEach(s=>{s.hidden=i==="sensors"}),i==="sensors"?Nc():ki&&Ho(ki),rh()}function lx(i){Rt=i;let e=pn?.querySelector(".map-wrap"),t=Q("world-map-sim-3d"),n=Q("world-map-sensor-2d"),r=Q("world-map-sensor-3d");pt==="simulation"?(e&&(e.hidden=i!=="2d"),t&&(t.hidden=i!=="3d"),e&&e.classList.toggle("is-3d",i==="3d"),ki&&i==="3d"&&requestAnimationFrame(()=>{Ln?.resize(),Ho(ki),Ln?.render()})):(n&&(n.hidden=i!=="2d"),r&&(r.hidden=i!=="3d"),i==="3d"&&requestAnimationFrame(()=>{Go(),ut&&Wo(ut,Ss),xe?.render()})),document.querySelectorAll("[data-render]").forEach(s=>s.setAttribute("aria-pressed",String(s.dataset.render===i))),rh()}function rh(){let i=Q("world-map-state");i&&(i.textContent=`${pt==="simulation"?"Simulation":"Live sensors"} \xB7 ${Rt.toUpperCase()}`);let e=pn?.querySelector(".map-wrap"),t=Q("world-map-sim-3d");e&&t&&pt==="simulation"&&(e.hidden=Rt!=="2d",t.hidden=Rt!=="3d")}window.addEventListener("body-worldmodel-viewchange",i=>ih(i.detail?.view==="sensors"?"sensors":"simulation"));window.addEventListener("resize",()=>{pt==="sensors"&&Rt==="3d"&&requestAnimationFrame(Go)});document.querySelectorAll("[data-render]").forEach(i=>i.addEventListener("click",()=>lx(i.dataset.render)));var sh=()=>{Ar?Po?.():Mx()};Q("world-map-midas-calibrate")?.addEventListener("click",sh);Q("world-map-midas-calibrate-3d")?.addEventListener("click",sh);document.querySelectorAll("[data-calibration-log-download]").forEach(i=>{i.addEventListener("click",vx)});document.querySelectorAll('.world-map-depth-calibration a[href="/body/camera/depth-calibration/log"]').forEach(i=>i.addEventListener("click",e=>{e.preventDefault(),bx()}));wx();ih(window.bodyWorldModelView==="sensors"?"sensors":"simulation");function cx(i,e,t){let n=Q("world-map-yolo-overlay");n.replaceChildren(),n.classList.remove("is-stale"),n.setAttribute("viewBox",`0 0 ${e} ${t}`);for(let r of i||[]){let s=r.bbox;if(!Array.isArray(s)||s.length<4)continue;let[a,o,c,l]=s.map(Number);if(![a,o,c,l].every(Number.isFinite))continue;let u=Number(r.overlayAgeS)>.5||r.overlaySourceStale,d=document.createElementNS("http://www.w3.org/2000/svg","rect");d.setAttribute("x",String(a*e)),d.setAttribute("y",String(o*t)),d.setAttribute("width",String(Math.max(0,c-a)*e)),d.setAttribute("height",String(Math.max(0,l-o)*t)),d.setAttribute("fill","none"),d.setAttribute("stroke",u?"#f2bc65":"#62f1c1"),d.setAttribute("opacity",u?"0.72":"1"),d.setAttribute("stroke-width",String(Math.max(e,t)*.004)),n.append(d);let h=document.createElementNS("http://www.w3.org/2000/svg","text");h.setAttribute("x",String(a*e)),h.setAttribute("y",String(Math.max(16,o*t-5))),h.setAttribute("fill","#dffff1"),h.setAttribute("font-size",String(Math.max(12,e*.026))),h.setAttribute("font-family","ui-monospace, monospace"),h.setAttribute("paint-order","stroke"),h.setAttribute("stroke","#07120f"),h.setAttribute("stroke-width",String(Math.max(2,e*.004)));let p=u?`LAST SEEN ${Math.max(0,Number(r.overlayAgeS)||0).toFixed(1)}s \xB7 `:"";h.textContent=`${p}${r.label||r.class_name||r.class||"object"} ${Math.round(Number(r.confidence||r.score||0)*100)}%`,n.append(h)}}function ah(i){let e=Number(i?.captured_at)>0?Date.now()/1e3-Number(i.captured_at):1/0;return!["ready","stale"].includes(i?.state)||e<0||e>2.5?[]:(i.detections||[]).filter(t=>{let n=Number(t.confidence??t.score??0),r=t.bbox;return n>=.25&&Array.isArray(r)&&r.length>=4&&r.slice(0,4).every(s=>Number.isFinite(Number(s)))})}function dx(i){return String(i.label||i.class_name||i.class||"object").toLowerCase()}function ux(i,e){if(!Array.isArray(i)||!Array.isArray(e))return 0;let[t,n,r,s]=i.map(Number),[a,o,c,l]=e.map(Number),u=Math.max(0,Math.min(r,c)-Math.max(t,a))*Math.max(0,Math.min(s,l)-Math.max(n,o)),d=Math.max(0,r-t)*Math.max(0,s-n),h=Math.max(0,c-a)*Math.max(0,l-o);return u/Math.max(1e-9,d+h-u)}function hx(i){let e=Date.now()/1e3,t=Number(i?.captured_at)||0,n=t>0?e-t:1/0,r=ah(i),s=String(i?.frame_id||t);if(s&&s!==zu&&r.length&&n>=0&&n<=2.5){zu=s;let a=new Set(Ui.map((o,c)=>c));for(let o of r){let c=dx(o),l=-1,u=.05;for(let h of a){let p=Ui[h];if(p.label!==c)continue;let g=ux(p.detection.bbox,o.bbox);g>u&&(u=g,l=h)}let d=l>=0?Ui[l]:{id:ix++,label:c,detection:o,lastSeenAt:t};l>=0&&a.delete(l),d.detection=o,d.lastSeenAt=t,d.sourceStale=i.state!=="ready"||i.paired===!1,l<0&&Ui.push(d)}}return Ui=Ui.filter(a=>e-a.lastSeenAt<=nx),Ui.map(a=>({...a.detection,overlayAgeS:e-a.lastSeenAt,overlaySourceStale:a.sourceStale}))}function fx(i){return i?.state!=="ready"||i?.paired===!1?[]:(i.detections||[]).filter(e=>{let t=Number(e.confidence??e.score??0),n=String(e.label||e.class_name||e.class||"");return t>=(/person|human/i.test(n)?.5:.45)})}function oh(i,e,t,n="image/jpeg"){t?(i.src=`data:${n};base64,${t}`,i.hidden=!1,e.hidden=!0):(i.removeAttribute("src"),i.hidden=!0,e.hidden=!1)}async function px(i){let e=Q("world-map-segmentation-overlay"),t=Q("world-map-segmentation-classes"),n=Q("world-map-segmentation-empty");if(!e||!t||!n)return;let r=i?.mask_png_base64,a=String(i?.frame_id||"")||String(i?.captured_at||"");if(!i?.available||!r){e.hidden=!0,n.hidden=!1,n.textContent=`${i?.state==="disabled"?"Enable SegFormer in Camera settings":`SegFormer ${i?.state||"waiting"}`}${i?.error?` \xB7 ${i.error}`:""}`,t.textContent="No semantic classes available",mc="";return}if(a===mc){e.hidden=!1,n.hidden=!0;return}let o=new Image;o.src=`data:image/png;base64,${r}`;try{await o.decode()}catch{return!1}if(a!==String(Rr?.frame_id||Rr?.captured_at||""))return;let c=document.createElement("canvas");c.width=o.naturalWidth,c.height=o.naturalHeight;let l=c.getContext("2d",{willReadFrequently:!0});l.drawImage(o,0,0);let u=l.getImageData(0,0,c.width,c.height).data;e.width=c.width,e.height=c.height;let d=e.getContext("2d"),h=d.createImageData(e.width,e.height),p=new Map;for(let x=0;x<u.length;x+=4){let m=u[x];if(!p.has(m)){let S=ju(m).getHexString();p.set(m,[parseInt(S.slice(0,2),16),parseInt(S.slice(2,4),16),parseInt(S.slice(4,6),16)])}let f=p.get(m);h.data[x]=f[0],h.data[x+1]=f[1],h.data[x+2]=f[2],h.data[x+3]=u[x+3]}d.putImageData(h,0,0),e.hidden=!1,n.hidden=!0,mc=a;let g=(i.classes||[]).slice(0,7).map(x=>{let m=document.createElement("span"),f=document.createElement("i");return f.style.backgroundColor=`#${ju(x.id).getHexString()}`,m.append(f,`${x.label} ${Math.round(Number(x.ratio||0)*100)}%`),m});t.replaceChildren(...g),g.length||(t.textContent="Mask available")}function mx(i,e=Yt){if(!e?.available)return i;let t=Number(e.inverse_scale_per_relative_unit)*i+Number(e.inverse_offset_per_m);if(!Number.isFinite(t)||t<=0)return null;let n=1/t;return Math.max(.2,Math.min(15,n))}function gx(i,e=Yt){if(!e?.available)return null;let t=Number(e.inverse_scale_per_relative_unit)*i+Number(e.inverse_offset_per_m);if(!Number.isFinite(t)||t<=0)return null;let n=1/t;if(!Number.isFinite(n)||n<.2||n>15)return null;let r=e.calibrated_relative_range||[],s=Math.min(Number(r[0]),Number(r[1])),a=Math.max(Number(r[0]),Number(r[1]));return{meters:n,extrapolated:!Number.isFinite(s)||!Number.isFinite(a)||i<s||i>a}}function lh(i,e){let t=Math.floor(e/4);if(i.rawValues&&Number.isFinite(i.rawValues[t]))return i.rawValues[t];let n=i.values[e]/255;return Number.isFinite(i.rawMin)&&Number.isFinite(i.rawMax)?i.rawMin+n*(i.rawMax-i.rawMin):n}function Cc(i,e,t){let n=lh(i,e),r=Number.isFinite(i.rawMin)&&Number.isFinite(i.rawMax);if(t?.available&&r){let a=mx(n,t);if(Number.isFinite(a))return a}let s=ch(i,Math.floor(e/4));return 1/bt.lerp(1/5.5,1/.7,s)}function ch(i,e){let t=e%i.width,n=Math.floor(e/i.width),r=[];for(let s=-1;s<=1;s++)for(let a=-1;a<=1;a++){let o=bt.clamp(t+a,0,i.width-1),l=bt.clamp(n+s,0,i.height-1)*i.width+o,u=i.normalizedDepth?.[l]??(i.normalizedValues?.[l*4]??i.values[l*4])/255;Number.isFinite(u)&&r.push(u)}return r.sort((s,a)=>s-a),bt.clamp(r[Math.floor(r.length/2)]??0,0,1)}function Vi(i){let e=kt?.intrinsics||kt?.camera_intrinsics||Zt?.intrinsics||Zt?.camera_intrinsics||{},t=Math.max(1,Number(i?.width)||640),n=Math.max(1,Number(i?.height)||480),r=Number(e.width||e.image_width||t),s=Number(e.height||e.image_height||n),a=t/r,o=n/s,c=Number(e.fx),l=Number(e.fy);if(c>0&&l>0&&Number.isFinite(Number(e.cx))&&Number.isFinite(Number(e.cy)))return{fx:c*a,fy:l*o,cx:Number(e.cx)*a,cy:Number(e.cy)*o,calibrated:!0};let u=t/(2*Math.tan(bt.degToRad(ws.horizontalFovDeg)/2));return{fx:u,fy:u,cx:(t-1)/2,cy:(n-1)/2,calibrated:!1}}function $t(i,e,t,n){return new D((i-n.cx)*t/n.fx,(n.cy-e)*t/n.fy,-t)}var Yu={low_body_front:{heightM:.12},level_body_front:{heightM:.35},high_body_front:{heightM:.65}};function Ts(){let i=kt?.camera_profile||"low_body_front",e=Yu[i]||Yu.low_body_front,t=Number(kt?.camera_height_m??kt?.calibration?.height_m??Zt?.camera_height_m),n=Number.isFinite(t)&&t>0&&t<3?t:e.heightM,r=Number(kt?.camera_pitch_deg??kt?.calibration?.pitch_deg??Zt?.camera_pitch_deg),s=Number.isFinite(r)?r:0,a=new Gt().setFromAxisAngle(new D(1,0,0),bt.degToRad(s));return{profile:i,heightM:n,rotation:a,position:new D(0,n,0)}}function Vo(i=_t){if(!xe)return;let e=Ts(),t=Ic(i);zi.quaternion.copy(t||new Gt);let n=Number(kt?.camera_height_m??kt?.calibration?.height_m??Zt?.camera_height_m),r=Number.isFinite(n)&&n>0,s=`${e.profile}:${e.heightM}:${r}`;s!==Xu&&(Xu=s,zi.position.set(0,e.heightM,0),Uo&&(Uo.scale.y=e.heightM/.18),Oo&&Oo.position.copy(e.position),ko("origin",[{position:e.position.clone(),text:`BODY SENSOR ORIGIN \xB7 ${e.heightM.toFixed(2)} m above floor${r?"":" nominal"}`}]),ko("camera-mount",[{position:e.position.clone(),text:`CAMERA MOUNT \xB7 ${e.profile.replace(/_/g," ")} \xB7 ${e.heightM.toFixed(2)} m${r?"":" nominal"}`}]))}Vo();function dh(i,e=_t){let t=new D(0,Ts().heightM,0),n=Ic(e),r=i.clone();return n&&r.applyQuaternion(n),r.add(t)}function qt(i,e=_t){let t=Ts();return dh(i.clone().applyQuaternion(t.rotation),e)}function uh(){if(!xe||!ut)return;let i=Vi(ut),e=ut.width,t=ut.height,n=xe.camera.near,r=xe.camera.far;xe.camera.projectionMatrix.makePerspective(-i.cx*n/i.fx,(e-i.cx)*n/i.fx,i.cy*n/i.fy,-(t-i.cy)*n/i.fy,n,r),xe.camera.projectionMatrixInverse.copy(xe.camera.projectionMatrix).invert()}async function hh(i){if(!i?.frame_id)return null;try{let e=await fetch(`/body/camera/yolo-frame?frame_id=${encodeURIComponent(i.frame_id)}`,{cache:"no-store"});if(!e.ok)return null;let t=await e.json(),n=t.camera||{};return t.available&&n.frame_id===i.frame_id&&n.image_base64?n:null}catch(e){return console.warn("Could not load camera pixels paired with MiDaS frame:",e),null}}async function xx(i){if(gi?.frame_id===i?.frame_id)return gi;if(!Number.isFinite(Number(i?.captured_at)))return null;try{let e=new URLSearchParams({nearest_to:String(i.captured_at),max_delta_s:String(Do)}),t=await fetch(`/body/camera/yolo/status?${e}`,{cache:"no-store"});if(!t.ok)return null;let n=await t.json(),r=Math.abs(Number(n.captured_at)-Number(i.captured_at));return n.state==="ready"&&Number.isFinite(r)&&r<=Do?{...n,frame_delta_s:r}:null}catch(e){return console.warn("Could not find YOLOX detections near MiDaS frame:",e),null}}async function fh(i){if(!xe||!i?.image_base64)return!1;let e=++Tc,t=new Image;if(t.src=`data:${i.mime_type||"image/jpeg"};base64,${i.image_base64}`,await t.decode(),e!==Tc)return!1;let n=Vi({width:t.naturalWidth,height:t.naturalHeight}),r=80,s=[qt($t(0,0,r,n),Number(i.captured_at)||_t),qt($t(t.naturalWidth,0,r,n),Number(i.captured_at)||_t),qt($t(0,t.naturalHeight,r,n),Number(i.captured_at)||_t),qt($t(t.naturalWidth,t.naturalHeight,r,n),Number(i.captured_at)||_t)],a=new Lt(t);a.colorSpace=Nt,a.needsUpdate=!0,Xt&&(xe.scene.remove(Xt),Xt.geometry.dispose(),Xt.material.map?.dispose(),Xt.material.dispose());let o=new ft;return o.setAttribute("position",new nt(s.flatMap(c=>c.toArray()),3)),o.setAttribute("uv",new nt([0,1,1,1,0,0,1,0],2)),o.setIndex([0,2,1,2,3,1]),Xt=new dt(o,new Wt({map:a,side:un,depthWrite:!1})),Xt.userData.frameId=i.frame_id,Xt.renderOrder=-1,Xt.visible=!!yt?.classList.contains("is-camera-view"),xe.scene.add(Xt),xe.render(),!0}async function ph(i){if(i?.depth_raw_png_base64&&Number.isFinite(Number(i.depth_raw_min))&&Number.isFinite(Number(i.depth_raw_max)))try{let n=await _x(i.depth_raw_png_base64);return n.rawMin=Number(i.depth_raw_min),n.rawMax=Number(i.depth_raw_max),n.frameId=String(i.frame_id||""),n.capturedAt=Number(i.captured_at)||0,n.workerReceivedAt=Number(i.worker_received_at)||0,n.publishedAt=Number(i.published_at)||0,n.browserFetchedAt=Number(i.browser_fetched_at)||0,n}catch(n){console.warn("Could not decode raw 16-bit MiDaS depth; using preview:",n)}let t=await Ix(i.depth_gray_jpeg_base64,"image/jpeg");return t.normalizedValues=t.values,t.frameId=String(i.frame_id||""),t.capturedAt=Number(i.captured_at)||0,t.workerReceivedAt=Number(i.worker_received_at)||0,t.publishedAt=Number(i.published_at)||0,t.browserFetchedAt=Number(i.browser_fetched_at)||0,t}async function _x(i){if(typeof DecompressionStream>"u")throw new Error("PNG decompression is unavailable");let e=Uint8Array.from(atob(i),T=>T.charCodeAt(0));if(![137,80,78,71,13,10,26,10].every((T,P)=>e[P]===T))throw new Error("Invalid PNG signature");let n=new DataView(e.buffer,e.byteOffset,e.byteLength),r=0,s=0,a=0,o=-1,c=0,l=[];for(let T=8;T+12<=e.length;){let P=n.getUint32(T),U=String.fromCharCode(...e.subarray(T+4,T+8)),F=T+8,k=F+P;if(k+4>e.length)throw new Error("Truncated PNG chunk");if(U==="IHDR"?(r=n.getUint32(F),s=n.getUint32(F+4),a=e[F+8],o=e[F+9],c=e[F+12]):U==="IDAT"&&l.push(e.subarray(F,k)),T=k+4,U==="IEND")break}if(!r||!s||a!==16||o!==0||c!==0)throw new Error("Expected non-interlaced 16-bit grayscale PNG");let u=l.reduce((T,P)=>T+P.length,0),d=new Uint8Array(u),h=0;for(let T of l)d.set(T,h),h+=T.length;let p=new Blob([d]).stream().pipeThrough(new DecompressionStream("deflate")),g=new Uint8Array(await new Response(p).arrayBuffer()),x=r*2;if(g.length!==(x+1)*s)throw new Error("Unexpected PNG scanline size");let m=new Uint8Array(x*s),f=(T,P,U)=>{let F=T+P-U,k=Math.abs(F-T),G=Math.abs(F-P),K=Math.abs(F-U);return k<=G&&k<=K?T:G<=K?P:U};for(let T=0;T<s;T++){let P=g[T*(x+1)],U=T*(x+1)+1,F=T*x;for(let k=0;k<x;k++){let G=g[U+k],K=k>=2?m[F+k-2]:0,W=T>0?m[F+k-x]:0,se=T>0&&k>=2?m[F+k-x-2]:0,de=P===0?0:P===1?K:P===2?W:P===3?Math.floor((K+W)/2):P===4?f(K,W,se):NaN;if(!Number.isFinite(de))throw new Error(`Unsupported PNG filter ${P}`);m[F+k]=G+de&255}}let S=new Float32Array(r*s),M=new Uint32Array(65536),y=Number.NaN,C=Number.NaN;for(let T=0;T<S.length;T++){let P=m[T*2]<<8|m[T*2+1];S[T]=P,M[P]++}let A=T=>{let P=Math.floor((S.length-1)*T),U=0;for(let F=0;F<M.length;F++)if(U+=M[F],U>P)return F;return 65535},I=A(.02),N=Math.max(I+1,A(.98)),v=new Float32Array(S.length),b=new Uint8ClampedArray(S.length*4);for(let T=0;T<S.length;T++){let P=bt.clamp((S[T]-I)/(N-I),0,1);v[T]=P;let U=Math.round(P*255),F=T*4;b[F]=b[F+1]=b[F+2]=U,b[F+3]=255}return{width:r,height:s,values:b,rawValues:S,normalizedDepth:v,rawMin:y,rawMax:C}}function yx(i){return new tn({transparent:!0,depthWrite:!1,uniforms:{uPointSize:{value:i},uViewportHeight:{value:xe?.renderer.domElement.height||1},uOpacity:{value:.92}},vertexShader:`
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
    `})}function zo(){let i=["world-map-midas-calibration-status","world-map-midas-calibration-status-3d"].map(Q).filter(Boolean);if(!i.length||Ar)return;let e;if(Fo)e=Fo;else if(an)e=an;else if(Yt?.available){let[t,n]=Yt.calibrated_range_m||[];e=`MiDaS fit \xB7 holdout \xB1${Number(Yt.holdout_rmse_m).toFixed(2)} m \xB7 ${Yt.sample_count} anchors \xB7 ${t}\u2013${n} m forward. Radar labels remain primary; camera alignment is approximate.`}else e="Not calibrated \xB7 ranges are relative, not metres. Track one person moving through several distances.";i.forEach(t=>{t.textContent=e})}async function vx(i){let e=["world-map-midas-calibration-status","world-map-midas-calibration-status-3d"].map(Q).filter(Boolean);(n=>{Fo=n,e.forEach(r=>{r.textContent=n})})("Opening the server download\u2026"),window.location.assign("/body/camera/depth-calibration/log")}async function bx(){let i=["world-map-midas-calibration-status","world-map-midas-calibration-status-3d"].map(Q).filter(Boolean),e=t=>{Fo=t,i.forEach(n=>{n.textContent=t})};e("Loading calibration log\u2026");try{let t=await fetch("/body/camera/depth-calibration/log",{cache:"no-store"});if(!t.ok)throw new Error(`HTTP ${t.status}`);let n=await t.text();if(!n)throw new Error("The log is empty");let r=Q("world-map-calibration-log-dialog");r||(r=document.createElement("dialog"),r.id="world-map-calibration-log-dialog",r.style.cssText="width:min(900px,94vw);max-height:88vh;padding:18px;background:#0a0f1a;color:#d7e4ed;border:1px solid #294153;border-radius:4px",r.innerHTML='<header style="display:flex;align-items:center;justify-content:space-between;gap:12px"><strong>MiDaS calibration log</strong><button type="button" data-log-close>Close</button></header><pre style="max-height:68vh;overflow:auto;white-space:pre-wrap;overflow-wrap:anywhere;background:#05070d;padding:12px;font:12px/1.45 ui-monospace,monospace"></pre><footer style="display:flex;gap:10px;align-items:center"><a href="/body/camera/depth-calibration/log" data-log-download>Download .log</a><small></small></footer>',r.querySelector("[data-log-close]").addEventListener("click",()=>r.close()),r.addEventListener("click",s=>{s.target===r&&r.close()}),document.body.append(r)),r.querySelector("pre").textContent=n,r.querySelector("footer small").textContent=`${new Blob([n]).size.toLocaleString()} bytes \xB7 ${n.split(/\r?\n/).filter(Boolean).length} records`,r.showModal(),e(`Log opened \xB7 ${n.split(/\r?\n/).filter(Boolean).length} records. Use Download .log or save this page's text.`)}catch(t){e(`Log could not be opened: ${t.message}`)}}async function wx(){try{let i=await fetch("/body/camera/depth-calibration",{cache:"no-store"});i.ok&&(Yt=await i.json())}catch(i){console.warn("Could not read persistent MiDaS calibration:",i)}zo()}function Jn(i,e){return String(i.id||i.target_id||`target-${e}`)}function Zu(i,e){let t=[...i].filter(o=>Number.isFinite(Number(o.timestamp))).sort((o,c)=>Number(o.timestamp)-Number(c.timestamp)),n=t.findIndex(o=>(o.targets||[]).some((c,l)=>Jn(c,l)===String(e)));if(n<0)return[];let r=null,s=0,a=[];for(let o of t.slice(n)){let c=Number(o.timestamp),l=(o.targets||[]).map((d,h)=>{let p=d.position_m||d.position||[],g=Number(p[0]),x=Number(p[1]);return{target:d,index:h,x:g,y:x}}).filter(d=>Number.isFinite(d.x)&&Number.isFinite(d.y));if(!l.length)continue;let u;if(!r)u=l.find(d=>Jn(d.target,d.index)===String(e));else{let d=l.map(p=>({...p,delta:Math.hypot(p.x-r.x,p.y-r.y)})).sort((p,g)=>p.delta-g.delta)[0],h=Math.min(1.75,Math.max(.55,(c-s)*.8+.25));d&&d.delta<=h&&(u=d)}u&&(r={x:u.x,y:u.y},s=c,a.push({sample:o,target:u.target,targetIndex:u.index}))}return a}function Pc(i,e,t=null,n=null,r={}){if(!String(e?.source||"").toLowerCase().startsWith("hlk_ld2450"))return[];let a=Number(r.minConfidence??.5),o=Number(r.maxBearingErrorDeg??tx),c=Number(r.ambiguityMarginDeg??3),l=Array.isArray(e.targets)?e.targets:[],u=(i||[]).filter(m=>/person|human/i.test(String(m.label||m.class_name||m.class||""))&&Number(m.confidence??m.score??0)>=a&&Array.isArray(m.bbox)&&m.bbox.length===4),d=[];for(let[m,f]of l.entries()){let S=Jn(f,m);if(n!=null&&S!==String(n))continue;let M=f.position_m||f.position;if(!Array.isArray(M)||M.length<2)continue;let y=Number(M[0]),C=Number(M[1]),A=Math.hypot(y,C);if(!Number.isFinite(A)||A<.25||A>6||C<=0||Math.abs(Math.atan2(y,C))>Math.PI/3)continue;let I=y-ws.lateralOffsetM,N=Math.atan2(I,C)-bt.degToRad(ws.yawOffsetDeg);for(let v of u){let b=(Number(v.bbox[0])+Number(v.bbox[2]))/2,T=Number(t?.width)||Number(kt?.width)||640,P=Vi({width:T,height:Number(t?.height)||480}),U=Math.atan2(b*T-P.cx,P.fx),F=bt.degToRad(ws.horizontalFovDeg);if(!r.skipFovGate&&Math.abs(U)>F/2)continue;let k=Math.abs((U-N)*180/Math.PI);k>o||d.push({detection:v,targetIndex:m,targetId:S,forward:C,radialRange:A,error:k,cost:k,lateralRight:I})}}d.sort((m,f)=>m.cost-f.cost);let h=d.filter(m=>{let f=d.filter(y=>y.detection===m.detection).sort((y,C)=>y.cost-C.cost),S=d.filter(y=>y.targetIndex===m.targetIndex).sort((y,C)=>y.cost-C.cost),M=y=>y[0]===m&&(!y[1]||y[1].cost-m.cost>=c);return M(f)&&M(S)}).sort((m,f)=>m.cost-f.cost),p=new Set,g=new Set;return h.filter(m=>p.has(m.detection)||g.has(m.targetIndex)?!1:(p.add(m.detection),g.add(m.targetIndex),!0))}function Mx(){if(Ar)return;let i=Q("world-map-calibration-guide");i||(i=document.createElement("dialog"),i.id="world-map-calibration-guide",i.className="world-map-calibration-guide",i.setAttribute("aria-labelledby","world-map-calibration-title"),i.innerHTML=`<form method="dialog" class="world-map-calibration-guide__surface">
      <header><div><p class="world-map-calibration-kicker">BODY \xB7 SENSOR CALIBRATION</p><h2 id="world-map-calibration-title">Radar + MiDaS calibration</h2></div><button class="world-map-calibration-close" value="cancel" aria-label="Close guide">\xD7</button></header>
      <p class="world-map-calibration-intro">Follow the stages in order. This action collects radar-matched MiDaS anchors; it does not calibrate camera intrinsics or physically measure sensor alignment for you.</p>
      <label class="world-map-calibration-target" for="world-map-calibration-radar-target">Radar target to calibrate<select id="world-map-calibration-radar-target" required><option value="">Waiting for live radar targets\u2026</option></select><small>Choose the radar track belonging to the person visible to YOLOX. The collector will ignore all other radar targets.</small></label>
      <ol class="world-map-calibration-stages">
        <li><b>0 \xB7 Prepare the rig</b><span>Rigidly fix camera, radar and IMU on a level floor. Measure camera height and camera-to-radar lateral offset. Mark 1\u20135 m on the camera axis and \xB11 m at 2 m and 4 m.</span></li>
        <li><b>1 \xB7 IMU zero, about 5 s</b><span>Keep the robot still. The live IMU must report valid attitude, ready gyro bias, stable calibration and roll/pitch within \xB15\xB0. For a real mount zero, record level-floor roll/pitch offsets; the current fit only gates on low tilt.</span></li>
        <li><b>2 \xB7 Camera intrinsics \xB7 manual prerequisite</b><span>Calibrate at the live 640\xD7480 resolution with 15\u201320 checkerboard views. Save fx, fy, cx, cy and distortion to calibration/camera.json; target RMS below 0.5 px (at most 1 px).</span></li>
        <li><b>3 \xB7 Camera \u2194 radar alignment \xB7 manual prerequisite</b><span>At each tape mark, match a person\u2019s camera bearing with radar atan2(x,y). Verify the mount yaw/lateral offset and keep error under 3\xB0. Current automatic matching uses an approximate field of view; it does not fit these offsets.</span></li>
        <li><b>4 \xB7 Ground-plane check \xB7 optional</b><span>With measured camera height and IMU mount pitch, compare visible foot-point ranges to the tape marks. Target error under 0.2 m at 1\u20134 m. Not currently calculated by this button.</span></li>
        <li><b>5 \xB7 Fit MiDaS to radar \xB7 automated here</b><span>Stand still at several 1\u20135 m marks. The selected radar track is paired with the nearest visible YOLO person; bearing is advisory until camera-to-radar alignment is measured. The fit needs 15 synchronized anchors across four distance bands and validates held-out data.</span></li>
        <li><b>6 \xB7 Validate \xB7 manual</b><span>Use tape marks omitted from fitting. Compare radar and MiDaS; test seated/cropped people too. Record the held-out RMSE. Treat predictions outside the fitted range as extrapolated.</span></li>
        <li><b>7 \xB7 Runtime</b><span>Radar remains the metric reference when a person is matched; MiDaS serves other objects. The rolling fit expires old anchors, so scene changes need fresh anchors. Recheck alignment after any impact/remount; redo intrinsics if lens or resolution changes.</span></li>
      </ol>
      <div class="world-map-calibration-checks"><label><input type="checkbox" data-calibration-check="rig"> Mounts are rigid; floor is level; tape marks are ready</label><label><input type="checkbox" data-calibration-check="imu"> Robot is stationary; IMU status is stable and low tilt</label><label><input type="checkbox" data-calibration-check="intrinsics"> I have verified the 640\xD7480 camera intrinsics</label><label><input type="checkbox" data-calibration-check="alignment"> I have measured/verified camera-to-radar alignment</label></div>
      <p class="world-map-calibration-caution">Intrinsics and alignment are not currently enforced by the fitter: without those checks, bearing matches and resulting distances remain approximate. Do not interpret a good MiDaS fit as proof of geometric calibration.</p>
      <p id="world-map-calibration-guide-status" class="world-map-calibration-progress" role="status">Ready when the robot and target person are stationary.</p>
      <footer><button type="button" data-calibration-action="cancel">Cancel</button><button type="button" data-calibration-action="start" class="primary">Start 60-second collection</button></footer>
    </form>`,document.body.appendChild(i),Rc(En),i.querySelector('[data-calibration-action="cancel"]')?.addEventListener("click",()=>i.close()),i.querySelector('[data-calibration-action="start"]')?.addEventListener("click",()=>{let e=[...i.querySelectorAll("[data-calibration-check]")].filter(r=>!r.checked),t=Q("world-map-calibration-guide-status"),n=Q("world-map-calibration-radar-target")?.value;if(!n){t.textContent="Select the radar target that matches the visible person before starting calibration.",Q("world-map-calibration-radar-target")?.focus();return}if(e.length){t.textContent=`Verify the ${e.length} unchecked prerequisite${e.length===1?"":"s"}, or cancel and complete those calibration stages first.`,e[0].focus();return}i.close(),Sx(n)}),i.addEventListener("click",e=>{e.target===i&&i.close()})),Rc(En),i.showModal()}function Rc(i){let e=Q("world-map-calibration-radar-target");if(!e)return;let t=e.value||e.dataset.selectedTargetId||"",n=Array.isArray(i?.targets)?i.targets:[],r=[new Option(n.length?"Select the person\u2019s radar target\u2026":"Waiting for live radar targets\u2026","")];n.forEach((s,a)=>{let o=Jn(s,a),c=s.position_m||s.position||[],l=Number(c[0]),u=Number(c[1]),d=`${s.id||s.target_id||`Target ${a+1}`} \xB7 ${Number.isFinite(u)?`${u.toFixed(2)} m forward`:"range \u2014"} \xB7 ${Number.isFinite(l)?`${l.toFixed(2)} m lateral`:"bearing \u2014"}`;r.push(new Option(d,o))}),t&&!n.some((s,a)=>Jn(s,a)===t)&&r.push(new Option(`Selected target ${t} \xB7 waiting for radar return`,t)),e.replaceChildren(...r),t&&(e.value=t),e.dataset.selectedTargetId=e.value,e.onchange=()=>{e.dataset.selectedTargetId=e.value}}async function Sx(i){if(Ar)return;let e=["world-map-midas-calibrate","world-map-midas-calibrate-3d"].map(Q).filter(Boolean),t=["world-map-midas-calibration-status","world-map-midas-calibration-status-3d"].map(Q).filter(Boolean);if(!e.length||!t.length)return;let n=fe=>t.forEach(Oe=>{Oe.textContent=fe});Ar=!0,an="",e.forEach(fe=>{fe.disabled=!1,fe.textContent="Cancel calibration"}),n(`Collecting target ${i} for up to 60 s. Move through four or more distance bands from 1\u20135 m; calibration stops when this capture ends.`);let r=[],s=[],a=new Map,o=new Map,c=globalThis.crypto?.randomUUID?.()||`midas-${Date.now()}-${Math.random().toString(36).slice(2,10)}`,l=[{type:"session_start",session_id:c,started_at:Date.now()/1e3,selected_target_id:i,window_seconds:60}],u=!1,d=0,h=!1,p=!1,g=null,x=new AbortController,m=!0,f=!1,S=setTimeout(()=>{x.abort(),e.forEach(fe=>{fe.disabled=!0,fe.textContent="Analyzing\u2026"}),n("60-second capture ended. Analyzing the samples and saving the log\u2026")},6e4);Po=()=>{f=!0,x.abort(),e.forEach(fe=>{fe.disabled=!0,fe.textContent="Stopping\u2026"}),n("Stopping capture and saving the diagnostic log\u2026")},e.forEach(fe=>{fe.onclick=Oe=>{Oe.preventDefault(),Po?.()}});let M=(fe,Oe,$e)=>Promise.race([fe,new Promise((Pe,X)=>setTimeout(()=>X(new Error(`${$e} timed out`)),Oe))]),y=new Set,C=new Set,A=new Set,I=new Set,N=new Set,v={depth:0,yolo:0,radar:0,framePairs:0,radarPairs:0,bearing:0,stationary:0,range:0,postFailures:0},b={minConfidence:.2,maxBearingErrorDeg:6,ambiguityMarginDeg:0},T=async(fe,Oe={})=>{let $e;for(let Pe=0;Pe<2;Pe+=1){if(m&&x.signal.aborted)throw new Error(f?"Cancelled by user":"Capture deadline reached");let X=new AbortController,J=setTimeout(()=>X.abort(),3e3),Y=()=>X.abort();m&&x.signal.addEventListener("abort",Y,{once:!0});try{let ae={...Oe,signal:X.signal},pe=await fetch(fe,ae);if(pe.status<500||Pe===1)return pe;$e=new Error(`HTTP ${pe.status}`)}catch(ae){if($e=ae,m&&x.signal.aborted)throw new Error(f?"Cancelled by user":"Capture deadline reached");if(Pe===1)throw $e}finally{clearTimeout(J),m&&x.signal.removeEventListener("abort",Y)}await new Promise(ae=>setTimeout(ae,150*(Pe+1)))}throw $e||new Error("Calibration request failed")},P=async(fe,Oe="")=>{let $e=performance.now();for(;h&&performance.now()-$e<3500;)await new Promise(Pe=>setTimeout(Pe,25));if(h)return{ok:!1,error:"Trace upload remained busy past 3.5 s"};if(fe&&!p&&(l.push({type:"session_end",session_id:c,ended_at:Date.now()/1e3,result:fe,error:Oe,depth_frames:s.length,radar_samples:a.size,selected_radar_samples:K,accepted_anchors:r.length,diagnostics:{...v}}),p=!0),d>=l.length)return{ok:!0,records_written:0};h=!0;try{let Pe=await fetch("/body/camera/depth-calibration/log",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({records:l.slice(d,d+5e3)}),signal:AbortSignal.timeout(3e3)});if(!Pe.ok)throw new Error(`HTTP ${Pe.status}`);let X=await M(Pe.json(),1500,"trace response");return X.ok&&(d+=Number(X.records_written)||0),u=p&&d>=l.length,X}catch(Pe){return{ok:!1,error:Pe.message}}finally{h=!1}},U="",F=null,k="",G=0,K=0,W=performance.now(),se=W+6e4,de=0,Ae=fe=>{fe.ok||(l.push({type:"trace_upload_failed",session_id:c,at:Date.now()/1e3,error:fe.error}),n(`Diagnostic log upload failed: ${fe.error}. Retrying while capture continues\u2026`))};P().then(Ae),g=setInterval(()=>{p||P().then(Ae)},5e3);try{for(;performance.now()<se&&!x.signal.aborted;){let Y=performance.now();if(Y-de>=1e3){de=Y;let Re=Math.floor((Y-W)/1e3),Ve=Math.max(0,Math.ceil((se-Y)/1e3)),E=Zu([...a.values()],i).length,_=new Set(r.map(z=>Math.min(4,Math.floor((z.forward_m-1)/.8)))).size;n(`Collecting \xB7 ${Re}s elapsed \xB7 ${Ve}s left \xB7 depth ${s.length} \xB7 radar ${E} \xB7 IMU ${o.size} \xB7 anchors ${r.length} \xB7 ${_}/4 bands.`)}for(let Re of Tr){let Ve=String(Re.sequence??Re.timestamp??"");Ve&&(a.set(Ve,Re),v.radar=a.size,y.has(Ve)||(y.add(Ve),l.push({type:"radar_sample",session_id:c,timestamp:Number(Re.timestamp),sequence:Re.sequence??null,source:Re.source||null,targets:(Re.targets||[]).map((E,_)=>({id:Jn(E,_),position_m:E.position_m||E.position||null,velocity_mps:E.velocity_mps||E.velocity||null}))})))}for(let Re of Oi){let Ve=String(Re.sequence??Re.timestamp??"");Ve&&(o.set(Ve,Re),C.has(Ve)||(C.add(Ve),l.push({type:"imu_sample",session_id:c,timestamp:Number(Re.timestamp),calibration_stable:!!Re.calibration_stable,attitude_valid:!!Re.attitude_valid,roll_deg:Number(Re.roll_deg),pitch_deg:Number(Re.pitch_deg)})))}let ae=new URL("/body/camera/depth",window.location.origin);ae.searchParams.set("include_raw","1"),ae.searchParams.set("include_preview","0"),ae.searchParams.set("include_color","0"),k&&ae.searchParams.set("since_frame_id",k);let pe;try{pe=await T(ae,{cache:"no-store"})}catch(Re){if(x.signal.aborted)break;l.push({type:"fetch_retry",source:"depth",at:Date.now()/1e3,error:Re.message}),n(`Temporary MiDaS fetch failure; keeping recorded data (${s.length} paired frames). Retrying\u2026`),await new Promise(Ve=>setTimeout(Ve,300));continue}if(!pe.ok){if(pe.status>=500){await new Promise(Re=>setTimeout(Re,100));continue}throw new Error(`MiDaS endpoint returned HTTP ${pe.status}`)}let Ce;try{Ce=await M(pe.json(),1500,"depth response")}catch{await new Promise(Re=>setTimeout(Re,150));continue}if(!Ce.frame_id||Ce.state!=="ready"||Ce.unchanged||!Ce.depth_raw_png_base64){n(`Waiting for live MiDaS depth \xB7 ${r.length} anchors collected.`),await new Promise(Re=>setTimeout(Re,200));continue}Ce.frame_id!==k&&(v.depth+=1,k=Ce.frame_id);let it=Number(Ce.captured_at),R=Date.now()/1e3;if(!Number.isFinite(it)||R-it>6){await new Promise(Re=>setTimeout(Re,100));continue}let qe;try{qe=await T(`/body/camera/yolo/status?frame_id=${encodeURIComponent(Ce.frame_id)}`,{cache:"no-store"}),qe.ok||(qe=await T(`/body/camera/yolo/status?nearest_to=${encodeURIComponent(Ce.captured_at)}&max_delta_s=${hc}`,{cache:"no-store"}))}catch(Re){if(x.signal.aborted)break;l.push({type:"fetch_retry",source:"yolox",at:Date.now()/1e3,error:Re.message,frame_id:Ce.frame_id,depth_at:it}),n(`Temporary YOLOX fetch failure; keeping ${s.length} recorded pairs. Retrying\u2026`),await new Promise(Ve=>setTimeout(Ve,300));continue}if(!qe.ok&&qe.status>=500){await new Promise(Re=>setTimeout(Re,100));continue}if(!qe.ok&&qe.status!==404)throw new Error(`YOLOX endpoint returned HTTP ${qe.status}`);let ue=qe.ok?await M(qe.json(),1500,"YOLOX response"):null;if(!ue||ue.state!=="ready"){await new Promise(Re=>setTimeout(Re,100));continue}let ye=Number(ue.captured_at),le=Math.abs(ye-it);I.has(ue.frame_id)||(v.yolo+=1,I.add(ue.frame_id));let Je=`${Ce.frame_id}|${ue.frame_id}`,_e=String(ue.frame_id||"")===String(Ce.frame_id);if(!N.has(Je)&&(_e||le<=hc)&&R-ye<=6&&(v.framePairs+=1,N.add(Je)),(_e||le<=hc)&&R-ye<=6&&R-it<=6&&!A.has(Je)){if(U!==Ce.frame_id){try{F=await M(ph(Ce),2e3,"depth decode")}catch{n(`Could not decode one depth frame; preserving ${s.length} recorded pairs.`),await new Promise(_=>setTimeout(_,100));continue}U=Ce.frame_id}let Re=(ue.detections||[]).filter(E=>/person|human/i.test(String(E.label||E.class_name||E.class||""))),Ve=[];for(let E of Re){let _=E.bbox.map(Number),z=Math.max(0,Math.min(F.width-1,Math.round((_[0]*.7+_[2]*.3)*F.width))),q=Math.max(z+1,Math.min(F.width,Math.round((_[0]*.3+_[2]*.7)*F.width))),j=Math.max(0,Math.min(F.height-1,Math.round((_[1]*.65+_[3]*.35)*F.height))),$=Math.max(j+1,Math.min(F.height,Math.round((_[1]*.35+_[3]*.65)*F.height))),Se=[],re=Math.max(1,Math.floor(Math.min(q-z,$-j)/8));for(let be=j;be<$;be+=re)for(let we=z;we<q;we+=re){let ee=lh(F,(be*F.width+we)*4);Number.isFinite(ee)&&ee>0&&Se.push(ee)}Se.length&&(Se.sort((be,we)=>be-we),Ve.push({detection:E,relativeDepth:Se[Math.floor(Se.length/2)]}))}s.push({depthAt:it,yoloAt:ye,frameId:Ce.frame_id,yoloFrameId:ue.frame_id,frameDelta:le,exactFrame:_e,people:Ve}),l.push({type:"vision_pair",session_id:c,depth_at:it,yolo_at:ye,frame_delta_s:le,exact_frame:_e,frame_id:Ce.frame_id,yolo_frame_id:ue.frame_id,people:Ve.map(E=>({class:E.detection.label||E.detection.class_name||E.detection.class,confidence:Number(E.detection.confidence??E.detection.score),bbox:E.detection.bbox.map(Number),relative_depth:E.relativeDepth}))}),A.add(Je)}await new Promise(Re=>setTimeout(Re,100))}if(m=!1,clearTimeout(S),f)throw l.push({type:"fit_status",session_id:c,available:!1,fit_reason:"cancelled_by_user"}),(await P("cancelled_by_user")).ok&&(an="Calibration cancelled; trace saved: data/body/midas_calibration_trace.log"),new Error("Cancelled by user");let Oe=Zu([...a.values()],i).map(({sample:Y,target:ae,targetIndex:pe})=>({...Y,targets:[ae],selected_track_target_id:Jn(ae,pe)}));K=Oe.length;let $e=[...o.values()].filter(Y=>Y.calibration_stable&&Y.attitude_valid&&Math.abs(Number(Y.roll_deg))<=5&&Math.abs(Number(Y.pitch_deg))<=5),Pe=new Set;for(let Y of s){let ae=Oe.reduce((ue,ye)=>{let le=Math.abs(Number(ye.timestamp)-(Y.depthAt+Y.yoloAt)/2);return!ue||le<ue.delta?{item:ye,delta:le}:ue},null);if(!ae||ae.delta>ex){let ue=[...a.values()].reduce((ye,le)=>{let Je=Number(le.timestamp),_e=Math.abs(Je-(Y.depthAt+Y.yoloAt)/2);return Number.isFinite(_e)&&(!ye||_e<ye.delta)?{item:le,delta:_e}:ye},null);l.push({type:"pair_rejected",session_id:c,depth_frame_id:Y.frameId,reason:ae?"selected_target_timestamp_outside_window":"selected_target_id_not_in_radar_history",selected_target_id:i,nearest_selected_delta_s:ae?.delta??null,nearest_any_delta_s:ue?.delta??null,available_target_ids:[...new Set([...a.values()].flatMap(ye=>(ye.targets||[]).map((le,Je)=>Jn(le,Je))))]});continue}v.radarPairs+=1;let pe=$e.reduce((ue,ye)=>{let le=Math.abs(Number(ye.timestamp)-Y.depthAt);return!ue||le<ue.delta?{item:ye,delta:le}:ue},null);if(!pe||pe.delta>1){l.push({type:"pair_rejected",session_id:c,depth_frame_id:Y.frameId,reason:"no_stable_imu_within_1s",radar_at:Number(ae.item.timestamp),radar_delta_s:ae.delta,imu_delta_s:pe?.delta??null});continue}v.stationary+=1;let Ce=Pc(Y.people.map(ue=>ue.detection),ae.item,null,ae.item.selected_track_target_id,b).find(ue=>ue.forward>=1&&ue.forward<=5);if(!Ce){l.push({type:"pair_rejected",session_id:c,depth_frame_id:Y.frameId,reason:"no_bearing_match_or_out_of_range",radar_at:Number(ae.item.timestamp),radar_delta_s:ae.delta,radar_targets:(ae.item.targets||[]).map((ue,ye)=>({id:Jn(ue,ye),position_m:ue.position_m||ue.position||null})),person_count:Y.people.length});continue}v.bearing+=1,v.range+=1;let it=String(ae.item.sequence??ae.item.timestamp);if(Pe.has(it))continue;let R=Y.people.find(ue=>ue.detection===Ce.detection);if(!R)continue;let qe={sample_id:`${Y.frameId}|${Y.yoloFrameId}|${i}|${it}`,selected_radar_target_id:String(ae.item.selected_track_target_id),selected_target_seed_id:String(i),selected_target_confirmed:!0,relative_depth:R.relativeDepth,forward_m:Ce.forward,bearing_error_deg:Ce.error,frame_delta_s:Y.frameDelta,frame_id_match:Y.exactFrame,radar_delta_s:ae.delta,imu_delta_s:pe.delta,stationary:!0};l.push({type:"pair_candidate",session_id:c,...qe,radar_sequence:ae.item.sequence??null}),Pe.add(it),r.push(qe)}e.forEach(Y=>{Y.disabled=!0,Y.textContent="Analyzing\u2026"}),n(`Analyzing ${s.length} frames \xB7 ${r.length} synchronized anchors \xB7 ${new Set(r.map(Y=>Math.min(4,Math.floor((Y.forward_m-1)/.8)))).size}/4 distance bands\u2026`);let X=null;if(r.length)try{let Y=await M(T("/body/camera/depth-calibration",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({samples:r})}),7e3,"anchor analysis");if(!Y.ok)throw new Error(`HTTP ${Y.status}`);X=await M(Y.json(),1500,"fit response"),G=Number(X.sample_count)||0,v.postFailures=X.accepted_count===r.length?0:r.length-Number(X.accepted_count||0),Yt=X.available?X:null,an=X.available?"":X.reason||"The recorded anchors did not validate.",zo()}catch(Y){throw v.postFailures=r.length,new Error(`Could not analyze the collected anchor batch: ${Y.message}`)}l.push({type:"fit_status",session_id:c,available:!!X?.available,fit:X});let J=await P(X?.available?"fit_validated":"fit_not_validated");if(J.ok?an=`Trace saved: data/body/midas_calibration_trace.log (${J.records_written} records)`:l.push({type:"trace_upload_failed",at:Date.now()/1e3,error:J.error}),!X?.available){let Y=v.framePairs===0?"No YOLOX/depth pairs met the 250 ms sync limit; check worker cadence and frame timestamps.":v.radarPairs===0?"No selected-target radar/depth pairs met the 4.5 s batch-match limit; verify that the selected track persists during the recording.":v.bearing===0?"No camera-person/radar bearing match; verify target identity, camera FOV, mount yaw and lateral offset.":v.stationary===0?"IMU did not confirm stable stationary posture; keep the body still and wait for gyro bias.":G<15?`Only ${G}/15 synchronized anchors were collected across ${new Set(r.map(ae=>Math.min(4,Math.floor((ae.forward_m-1)/.8)))).size}/4 distance bands. Pause at each of four or more distinct 1\u20135 m distances.`:an||"The anchors did not span four distinct distance bands or failed holdout validation. Pause at each distance mark and keep the selected person still.";throw new Error(`Fit not validated; collected ${G} anchors. ${Y}`)}Cr="",an="",Mc=0,Dc().catch(Y=>console.warn("Depth refresh after calibration failed",Y))}catch(fe){m=!1,clearTimeout(S),l.push({type:"fit_status",session_id:c,available:!1,fit_reason:fe.message});let Oe=u?{ok:!0}:await M(P(f?"cancelled_by_user":"collector_error",fe.message),4e3,"final trace upload").catch($e=>({ok:!1,error:$e.message}));if(f){an=`Calibration cancelled \xB7 recorded ${s.length} depth/YOLO frames \xB7 trace ${Oe.ok?"saved":`upload failed: ${Oe.error}`}`,n(an);return}an=`Calibration not saved: ${fe.message} \xB7 recorded frames ${s.length}, YOLO/depth pairs \u2264250 ms ${v.framePairs}, radar samples ${v.radar} (${K} selected), radar pairs \u22641.25 s ${v.radarPairs}, bearing matches \u22646\xB0 ${v.bearing}, stable IMU pairs \u22641 s ${v.stationary}, in-range ${v.range}, anchor upload failures ${v.postFailures}`,Oe.ok&&(an+=" \xB7 trace: data/body/midas_calibration_trace.log"),n(an)}finally{m=!1,clearTimeout(S),clearInterval(g),Po=null,Ar=!1,e.forEach(fe=>{fe.onclick=null,fe.disabled=!1,fe.textContent=Yt?.available?"Recalibrate with radar":"Start calibration"}),zo()}}async function Nc(){if(!(xc||pt!=="sensors")){xc=!0;try{let e=await(await fetch("/body/camera/frame",{cache:"no-store"})).json();Lo("camera",!1);let t=e.camera||{},n=e.yolo||{};kt=t,Vo(),gi=n;let r=Q("world-map-camera-state"),s=Number(t.captured_at)>0?Math.max(0,Date.now()/1e3-Number(t.captured_at)):1/0;r&&(r.textContent=t.image_base64?`LIVE \xB7 ${t.width||"\u2014"}\xD7${t.height||"\u2014"} \xB7 ${Number.isFinite(s)?s.toFixed(1)+"s":"age \u2014"}`:`${t.state||e.status||"NO FRAME"}`),At("world-map-camera-state","camera",jn("camera",s,!!t.image_base64),t.image_base64?`LIVE \xB7 ${t.width||"\u2014"}\xD7${t.height||"\u2014"} \xB7 ${Number.isFinite(s)?s.toFixed(1)+"s":"age \u2014"}`:`${t.state||e.status||"NO FRAME"}`);let a=Q("world-map-camera-image"),o=Q("world-map-camera-empty");t.frame_id!==Ou&&(oh(a,o,t.image_base64,t.mime_type||"image/jpeg"),Ou=t.frame_id);let c=a?.parentElement;c&&t.width&&t.height&&(c.style.aspectRatio=`${t.width}/${t.height}`);let l=hx(n),u=Number(n.captured_at)>0?Date.now()/1e3-Number(n.captured_at):1/0,d=`${n.state||"disabled"}:${n.frame_id||""}:${l.map(m=>`${m.overlayAgeS.toFixed(1)}:${m.bbox.join(",")}`).join(";")}`;d!==Bu&&(cx(l,t.width||640,t.height||480),Bu=d),Rt==="3d"&&ut&&Wo(ut,Ss),Rt==="3d"&&Kn();let h=`${n.state||"disabled"} \xB7 ${(n.detections||[]).length} boxes${n.latency_ms!=null?` \xB7 ${n.latency_ms} ms`:""}${n.paired===!1?" \xB7 waiting for paired frame":""}`,p=n.paired===!1&&n.state==="stale"?"stale":jn("yolo",u,n.state==="ready"&&!!t.image_base64&&n.paired!==!1);At("world-map-yolo-state","yolo",p,h);let g=t.frame_id?`${t.frame_id}${t.captured_at?` \xB7 ${s.toFixed(1)}s`:""}`:"No frame";Q("world-map-frame-state").textContent=g;let x=Q("world-map-summary-frame");x&&(x.textContent=Number.isFinite(s)?`${s.toFixed(1)} s`:"\u2014"),Q("world-map-sensor-note").textContent=`Sensor-only view \xB7 frame ${t.frame_id||"unavailable"} \xB7 no simulation object positions or metric scale.`}catch(i){At("world-map-camera-state","camera","offline",`Offline \xB7 ${i.message}`),At("world-map-yolo-state","yolo","offline","Offline \xB7 waiting for camera frame"),Lo("camera",!0),Q("world-map-sensor-note").textContent=kt?.frame_id?`Sensor-only view \xB7 last camera frame ${kt.frame_id} is retained but not current.`:"Sensor-only view \xB7 waiting for a current camera frame."}finally{xc=!1}}}async function As(i){let e=await fetch(i,{cache:"no-store"});if(!e.ok)throw new Error(`HTTP ${e.status}`);return e.json()}var mn={radar:!1,gps:!1,imu:!1,tof:!1},vc=!1,St=(i,e=1,t="")=>{let n=i==null||i===""?NaN:Number(i);return Number.isFinite(n)?`${n.toFixed(e)}${t}`:"\u2014"};async function Ex(){if(!(vc||pt!=="sensors")){vc=!0;try{let i=await As("/system/metrics"),e=i.cpu||{},t=i.gpu||{},n=i.memory||{},r=i.power||{};Q("world-map-system-state").textContent=i.available?"Live \xB7 1 s":"Partial telemetry";let s=(h,p,g,x,m="")=>{let f=Q(h),S=p!=null&&p!==""&&Number.isFinite(Number(p)),M=S?Math.max(0,Math.min(Number(g),Number(p))):0;f.style.setProperty("--gauge-value",S?String(M/Number(g)*100):"0"),f.setAttribute("aria-label",`${x}: ${S?`${Number(p).toFixed(1)}${m}`:"unavailable"}`)};s("world-map-cpu-gauge",e.utilization_percent,100,"CPU utilization","%"),s("world-map-cpu-temp-gauge",e.temperature_c,100,"Maximum CPU temperature"," degrees Celsius"),s("world-map-gpu-temp-gauge",t.temperature_c,100,"Maximum GPU temperature"," degrees Celsius"),s("world-map-memory-gauge",n.used_percent,100,"Memory utilization","%"),Q("world-map-system-cpu-value").textContent=e.utilization_percent==null?"\u2014":e.utilization_percent.toFixed(0),Q("world-map-system-cpu-temp-value").textContent=St(e.temperature_c,1),Q("world-map-system-gpu-temp-value").textContent=St(t.temperature_c,1),Q("world-map-system-cpu-temp").textContent=`Hottest CPU \xB7 ${St(e.temperature_c,1,"\xB0C")}`;let a=t.frequency_mhz==null?"\u2014":`${t.frequency_mhz.toFixed(0)} MHz`;Q("world-map-system-gpu-meta").textContent=`${t.utilization_percent==null?"Load unavailable":`${t.utilization_percent.toFixed(1)}% load`} \xB7 ${a}`,Q("world-map-system-gpu-load").textContent=t.utilization_percent==null?"Not exposed by kernel":`${t.utilization_percent.toFixed(1)}%`,Q("world-map-system-gpu-clock").textContent=a,Q("world-map-system-memory-value").textContent=n.used_percent==null?"\u2014":n.used_percent.toFixed(0),Q("world-map-system-memory-meta").textContent=n.available_mb==null?"Free memory unavailable":`${(n.available_mb/1024).toFixed(1)} / ${(n.total_mb/1024).toFixed(1)} GB free`;let o=Math.max(20,Math.ceil((Number(r.watts)||0)/10)*10);s("world-map-power-gauge",r.watts,o,"Measured board input power"," watts"),Q("world-map-power-gauge").setAttribute("aria-label",r.available?`Measured board input power: ${r.watts.toFixed(2)} watts on a 0 to ${o} watt display scale`:"Measured board input power unavailable"),Q("world-map-system-power-value").textContent=r.available?r.watts.toFixed(1):"\u2014";let c=Q("world-map-summary-power"),l=Q("world-map-summary-energy");c&&(c.textContent=r.available?`${r.watts.toFixed(1)} W`:"\u2014 W"),l&&(l.textContent=r.available?`${r.energy_wh_session.toFixed(3)} Wh`:"\u2014 Wh"),Q("world-map-system-power-meta").textContent=r.available?`${r.voltage_v.toFixed(1)} V \xB7 ${r.current_a.toFixed(2)} A \xB7 scale 0\u2013${o} W`:"Onboard power monitor unavailable";let u=String(gi?.runtime||"").toLowerCase().includes("htp"),d=String(Zt?.device||"").toLowerCase().includes("htp");Q("world-map-system-htp").textContent=u||d?`ACTIVE \xB7 YOLOX ${u?`${St(gi?.inference_ms,0," ms")} HTP`:"\u2014"} \xB7 MiDaS ${d?`${St(Zt?.inference_ms,0," ms")} HTP`:"\u2014"}`:"Utilization counter unavailable",Q("world-map-system-energy").textContent=r.available?`${r.energy_wh_session.toFixed(3)} Wh`:"Unavailable",Q("world-map-system-note").textContent="The INA232 monitors the onboard input rail; external motor loads may be excluded. Temperature dials show the hottest reported sensor in each group; GPU/HTP utilization is unavailable because the kernel exports no reliable busy counter."}catch(i){Q("world-map-system-state").textContent=`Unavailable \xB7 ${i.message}`}finally{vc=!1}}}function Ju(i={}){let e=Q("world-map-radar-plot"),t=e?.getContext("2d");if(!t)return;let n=Math.min(window.devicePixelRatio||1,2),r=Math.max(1,e.clientWidth),s=Math.max(1,e.clientHeight);(e.width!==Math.round(r*n)||e.height!==Math.round(s*n))&&(e.width=Math.round(r*n),e.height=Math.round(s*n)),t.setTransform(n,0,0,n,0,0),t.clearRect(0,0,r,s);let a=38,o=r-22,c=18,l=s-28,u=(a+o)/2;t.strokeStyle="#294c3a",t.fillStyle="#8eaa98",t.font="10px ui-monospace,monospace";for(let h=1;h<=6;h+=1){let p=l-(l-c)*h/6;t.globalAlpha=h%2?.55:.9,t.beginPath(),t.moveTo(a,p),t.lineTo(o,p),t.stroke(),t.fillText(`${h}m`,6,p+3)}t.globalAlpha=1;for(let h=-60;h<=60;h+=30){let p=u+Math.tan(h*Math.PI/180)/Math.tan(Math.PI/3)*(o-a)/2;t.beginPath(),t.moveTo(p,c),t.lineTo(p,l),t.stroke(),t.fillText(`${h>0?"+":""}${h}\xB0`,p-10,s-8)}t.fillStyle="#b6f1d3",t.beginPath(),t.moveTo(u,l-9),t.lineTo(u-6,l+1),t.lineTo(u+6,l+1),t.closePath(),t.fill();let d=Array.isArray(i.targets)?i.targets:[];for(let h of d){let p=h.position_m||h.position||[],g=Number(p[0]),x=Number(p[1]);if(!Number.isFinite(g)||!Number.isFinite(x)||x<0||x>6)continue;let m=Math.atan2(g,x);if(Math.abs(m)>Math.PI/3)continue;let f=u+m/(Math.PI/3)*(o-a)/2,S=l-x/6*(l-c),M=Number(h.radial_speed_mps),y=Number(fn?.captured_at)>0?Date.now()/1e3-Number(fn.captured_at):1/0,C=fn?.available&&y<=.35&&Number(fn.confidence)>=.35&&Number(fn.speed_mps)>=.05,A=Number.isFinite(M)&&Math.abs(M)>=.05&&!C;t.fillStyle=C?"#9aa7ad":A?"#ed91c5":"#efcb76",t.beginPath(),t.arc(f,S,5,0,Math.PI*2),t.fill(),t.fillStyle="#e7f4eb",t.font="10px ui-monospace,monospace",t.fillText(`${x.toFixed(1)}m`,f+8,S-5)}}async function mh(){if(!(pt!=="sensors"||mn.radar)){mn.radar=!0;try{let i=await As("/plugins/mmwave_radar/status"),e=i.sample||{};En=i.available?e:null,En?.timestamp&&!Tr.some(a=>a.timestamp===En.timestamp)&&(Tr.push(En),Tr=Tr.filter(a=>Date.now()/1e3-Number(a.timestamp)<=12).slice(-128));let t=Array.isArray(e.targets)?e.targets:[];Rc(En);let n=Number(e.timestamp)>0?Math.max(0,Date.now()/1e3-Number(e.timestamp)):NaN,s=`${`${t.length} target${t.length===1?"":"s"}`}${Number.isFinite(n)?` \xB7 ${n.toFixed(1)} s`:""}`;At("world-map-radar-state","radar",jn("radar",n,!!i.available),i.available?s:i.error||"No data"),Q("world-map-radar-targets").replaceChildren(...t.length?t.map((a,o)=>{let c=a.position_m||a.position||[],l=a.velocity_mps||a.velocity||[],u=Number(c[0]),d=Number(c[1]),h=document.createElement("div");h.className="sensor-target-row";let p=document.createElement("span");p.textContent=`${a.id||a.target_id||`Target ${o+1}`} \xB7 ${a.classification||"unclassified"}`;let g=document.createElement("b");return g.textContent=`${Number.isFinite(d)?d.toFixed(2):"\u2014"} m fwd \xB7 ${Number.isFinite(u)?u.toFixed(2):"\u2014"} m lat \xB7 ${St(a.radial_speed_mps,2," m/s")}`,h.append(p,g),h.title=`XY velocity ${St(l[0],2)} / ${St(l[1],2)} m/s \xB7 confidence ${St(a.confidence,2)}`,h}):[Object.assign(document.createElement("span"),{textContent:i.available?"No targets in current radar frame.":"Waiting for a live radar frame."})]),Ju(e),Hi(En)}catch(i){En=null,At("world-map-radar-state","radar","offline",`Unavailable \xB7 ${i.message}`),Q("world-map-radar-state").textContent=`Unavailable \xB7 ${i.message}`,Q("world-map-radar-targets").textContent="No live radar data.",Ju(),Hi(null)}finally{mn.radar=!1}}}async function gh(){if(!(pt!=="sensors"||mn.gps)){mn.gps=!0;try{let i=await As("/plugins/gps/status"),e=i.sample||i.source_status?.sample||{},t=i.source_status?.diagnostic||{},n=!!(i.available||e.connected||Number(t.bytes_received)>0),r=e.fix===!0||e.valid===!0||Number(e.fix_quality)>0,s=Number(e.timestamp)>0?Math.max(0,Date.now()/1e3-Number(e.timestamp)):NaN,a=jn("gps",s,n);At("world-map-gps-state","gps",a,r?"Fix valid":n?"UART live \xB7 no fix":i.error||"Offline");let o=Number(e.latitude_deg??e.latitude??e.lat),c=Number(e.longitude_deg??e.longitude??e.lon??e.lng);Q("world-map-gps-position").textContent=r&&Number.isFinite(o)&&Number.isFinite(c)?`${o.toFixed(6)}, ${c.toFixed(6)}`:"No valid fix",Q("world-map-gps-fix").textContent=`${a==="stale"?"Stale fix":a==="live"&&r?"Valid":"No fix"} \xB7 quality ${e.fix_quality??"\u2014"}`,Q("world-map-gps-satellites").textContent=`${e.satellites??"\u2014"} used \xB7 ${e.satellites_in_view??"\u2014"} in view`,Q("world-map-gps-quality").textContent=`HDOP ${St(e.hdop)} \xB7 ${St(e.altitude_m,1," m")}`;let l=Array.isArray(e.satellite_signals)?e.satellite_signals:[],u=Q("world-map-gps-signals");u.setAttribute("aria-label",`GPS satellite signal strength; ${l.length} satellites reported`);let d=l.slice(0,12),h=d.map(p=>{let g=Number(p.cn0_db_hz),x=Number.isFinite(g)?Math.max(3,Math.min(60,g)):3,m=document.createElement("div");m.className="sensor-gps-bar";let f=`${String(p.talker||"GN").replace(/[^a-z0-9]/gi,"")}-${Number(p.svid)||"?"}`,S=document.createElement("span");S.textContent=Number.isFinite(g)?g.toFixed(0):"\u2014";let M=document.createElement("i");M.style.height=`${x}px`,M.style.background=g>=35?"#3d9f70":g>=25?"#c39738":"#bd6559";let y=document.createElement("small");return y.textContent=f,m.title=`${f} \xB7 C/N\u2080 ${St(g,0," dB-Hz")} \xB7 az ${p.azimuth_deg??"\u2014"}\xB0 \xB7 el ${p.elevation_deg??"\u2014"}\xB0`,m.append(S,M,y),m});if(l.length>d.length){let p=document.createElement("span");p.className="sensor-gps-more",p.textContent=`+${l.length-d.length}`,p.title=`${l.length-d.length} additional satellites`,h.push(p)}u.replaceChildren(...l.length?h:[Object.assign(document.createElement("span"),{className:"sensor-readout-note",textContent:i.available?"No GSV satellite signal values in the current GPS sample.":"Waiting for GSV data from the GPS receiver."})])}catch(i){At("world-map-gps-state","gps","offline",`Unavailable \xB7 ${i.message}`)}finally{mn.gps=!1}}}async function xh(){if(!(pt!=="sensors"||mn.imu)){mn.imu=!0;try{let i=await As("/plugins/imu/status"),e=i.sample||{};Array.isArray(i.history)?Oi=i.history.slice(-256):e.sequence!=null&&!Oi.some(a=>a.sequence===e.sequence)&&(Oi.push(e),Oi=Oi.slice(-256));let t=Number(e.timestamp)>0?Math.max(0,Date.now()/1e3-Number(e.timestamp)):NaN;At("world-map-imu-state","imu",jn("imu",t,!!i.available),i.available?`${e.attitude_valid?"Fused attitude":"Fused attitude unavailable"} \xB7 ${e.motion_state||"motion unknown"}${e.gyro_bias_ready?" \xB7 bias ready":" \xB7 bias warming"}`:i.error||"No data"),Q("world-map-imu-roll").textContent=e.attitude_valid?St(e.roll_deg,1,"\xB0"):"Invalid",Q("world-map-imu-pitch").textContent=e.attitude_valid?St(e.pitch_deg,1,"\xB0"):"Invalid";let n=Q("world-map-imu-attitude");if(n){let a=Number(e.roll_deg),o=Number(e.pitch_deg),c=!!e.attitude_valid&&Number.isFinite(a)&&Number.isFinite(o);n.dataset.state=c?"live":"offline",c&&(n.style.setProperty("--imu-roll",`${a}deg`),n.style.setProperty("--imu-pitch",`${Math.max(-18,Math.min(18,o*.7))}px`))}Q("world-map-imu-yaw").textContent=`${St(e.yaw_relative_deg,1,"\xB0")} rel \xB7 ${St(e.yaw_rate_dps??e.angular_velocity_dps?.[2],1,"\xB0/s")}`;let r=e.acceleration_g;Q("world-map-imu-accel").textContent=Array.isArray(r)?r.map(a=>St(a,2)).join(" / "):"\u2014";let s=e.angular_velocity_dps;Q("world-map-imu-gyro").textContent=Array.isArray(s)?s.map(a=>St(a,1)).join(" / "):"\u2014"}catch(i){At("world-map-imu-state","imu","offline",`Unavailable \xB7 ${i.message}`)}finally{mn.imu=!1}}}async function _h(){if(!(pt!=="sensors"||mn.tof)){mn.tof=!0;try{let i=await As("/plugins/tof/status"),e=i.sample||{},t=Number(e.timestamp)>0?Math.max(0,Date.now()/1e3-Number(e.timestamp)):NaN,n=i.available&&e.available!==!1&&!e.simulated&&!/sensor_not_detected/i.test(String(i.error||"")),r=jn("tof",t,n);At("world-map-tof-state","tof",r,r==="stale"?`Stale \xB7 ${t.toFixed(1)} s`:n?`${e.device||i.sensor||"VL53L1X"} \xB7 live`:i.error||"No fresh measurement"),Q("world-map-tof-distance").textContent=n?St(e.distance_m,2," m"):"No measurement",Q("world-map-tof-meta").textContent=n?`${e.frame||i.frame||"body_front"} \xB7 ${St(e.distance_mm,0," mm")}`:i.transport||"Forward single-beam range"}catch(i){At("world-map-tof-state","tof","offline",`Unavailable \xB7 ${i.message}`)}finally{mn.tof=!1}}}async function Tx(){if(!(_c||pt!=="sensors")){_c=!0;try{let e=await(await fetch("/body/camera/segmentation",{cache:"no-store"})).json();if(Rr=e,px(e).catch(n=>{let r=Q("world-map-segmentation-classes");r&&(r.textContent=`SegFormer mask unavailable \xB7 ${n.message}`)}),Q("world-map-segmentation-state")){let n=Number(e.captured_at)>0?Math.max(0,Date.now()/1e3-Number(e.captured_at)):NaN,r=Number.isFinite(n)?` \xB7 ${n.toFixed(1)}s old`:"",s=!!(e.available||e.mask_png_base64||e.class_mask),a=jn("segmentation",n,s&&e.state!=="disabled");At("world-map-segmentation-state","segmentation",a,`${e.state||"disabled"}${e.device?` \xB7 ${e.device}`:""}${e.latency_ms!=null?` \xB7 ${e.latency_ms} ms`:""}${r}`)}}catch(i){Q("world-map-segmentation-state")&&At("world-map-segmentation-state","segmentation","offline",`SegFormer unavailable \xB7 ${i.message}`)}finally{_c=!1}}}async function Dc(){if(!(pc||pt!=="sensors"||Zt&&performance.now()-Mc<100)){pc=!0;try{let i=Rt==="3d"?Cr:String(Q("world-map-depth-image")?.dataset.frameId||""),e=new URLSearchParams({include_raw:Rt==="3d"&&Yt?.available?"1":"0",include_preview:"1",include_color:Rt==="3d"?"0":"1"});i&&e.set("since_frame_id",i);let n=await(await fetch(`/body/camera/depth?${e}`,{cache:"no-store"})).json();Lo("depth",!1);let r=Rr;Zt=n,Rr=r,Mc=performance.now();let s=Number(n.captured_at)>0?` \xB7 ${Math.max(0,Date.now()/1e3-Number(n.captured_at)).toFixed(1)}s old`:"",a=Number(n.captured_at)>0?Math.max(0,Date.now()/1e3-Number(n.captured_at)):NaN,o=jn("midas",a,!!n.available&&n.state!=="disabled");if(At("world-map-midas-state","midas",o,`${n.state||"disabled"}${n.device?` \xB7 ${n.device}`:""}${n.latency_ms!=null?` \xB7 ${n.latency_ms} ms`:""}${s}${n.error?` \xB7 ${n.error}`:""}`),n.unchanged||!n.frame_id){Kn();return}n.browser_fetched_at=Date.now()/1e3,at&&(at.material.uniforms.uOpacity.value=.92),zo();let c=wh(r,n)?String(r.frame_id||r.captured_at||""):"",l=`${n.frame_id||""}:${Number(n.captured_at)||0}:${c}`,u=`${Cr}:${_t}:${Sc}`,d=Rt==="3d"&&l!==u&&l!==Io,h=Rt!=="3d"&&n.frame_id&&Q("world-map-depth-image")?.dataset.frameId!==String(n.frame_id);if((d||h)&&n.frame_id){let p=String(n.frame_id);if(n.depth_jpeg_base64&&(oh(Q("world-map-depth-image"),Q("world-map-depth-empty"),n.depth_jpeg_base64),Q("world-map-depth-image").dataset.frameId=p),d&&n.depth_gray_jpeg_base64){Io=l;try{await Px(n,r)&&(Cr=p,Sc=c)}finally{Io===l&&(Io="")}}}}catch(i){At("world-map-midas-state","midas","offline",`unavailable \xB7 ${i.message}`),at&&(at.visible=!1,xe.render()),Lo("depth",!0)}finally{pc=!1}}}var bc=!1;async function Ax(){if(!(bc||pt!=="sensors")){bc=!0;try{let e=await(await fetch("/body/odometry/visual",{cache:"no-store"})).json();if(!Q("world-map-odometry-state"))return;let n=Q("world-map-odometry-map-status");n&&(n.textContent=e.available?"TRACKING":`${String(e.state||"waiting").toUpperCase()} \xB7 LAST FIX RETAINED`,n.title=e.reason||"");let r=Number(e.captured_at)>0?Math.max(0,Date.now()/1e3-Number(e.captured_at)):NaN,s=jn("odometry",r,!!e.available);if(e.available){let[a=0,o=0]=e.position_m||[];At("world-map-odometry-state","odometry",s,`${a.toFixed(2)}m fwd \xB7 ${o.toFixed(2)}m left \xB7 ${Math.round(e.confidence*100)}% \xB7 experimental`);let c=String(e.frame_id||"");c&&c!==ku&&(ku=c,Zn.push({forward:a,lateral:o}),Zn.length>600&&Zn.shift(),Es()),Cx(e)}else At("world-map-odometry-state","odometry","offline",`${e.state||"waiting"} \xB7 ${e.reason||"need synchronized camera, MiDaS and radar calibration"}`),n&&(n.title=e.reason||"")}catch(i){Q("world-map-odometry-state")&&At("world-map-odometry-state","odometry","offline",`unavailable \xB7 ${i.message}`)}finally{bc=!1}}}function Cx(i){fn=i,yh();let e=Q("world-map-odometry-map-status");e&&(e.textContent=`TRACKING \xB7 ${Number(i.speed_mps||0).toFixed(2)} m/s`)}function yh(){let i=Q("world-map-odometry-map"),e=i?.parentElement;if(!i||!e)return;let t=e.getBoundingClientRect();if(!t.width||!t.height)return;let n=Math.max(1,window.devicePixelRatio||1),r=Math.round(t.width*n),s=Math.round(t.height*n);(i.width!==r||i.height!==s)&&(i.width=r,i.height=s);let a=i.getContext("2d");a.setTransform(n,0,0,n,0,0);let o=t.width,c=t.height;a.fillStyle="#050b12",a.fillRect(0,0,o,c),a.strokeStyle="#1b3042",a.lineWidth=1;for(let M=0;M<=o;M+=Math.max(48,o/8))a.beginPath(),a.moveTo(Math.round(M)+.5,0),a.lineTo(Math.round(M)+.5,c),a.stroke();for(let M=0;M<=c;M+=Math.max(40,c/6))a.beginPath(),a.moveTo(0,Math.round(M)+.5),a.lineTo(o,Math.round(M)+.5),a.stroke();let l=Math.min(28,o*.08),u={left:l,right:o-l,top:l,bottom:c-l},d={x:o/2,y:c*.68},h=Math.max(1,...Zn.map(M=>Math.abs(M.forward))),p=Math.max(1.4,...Zn.map(M=>Math.abs(M.lateral))),g=Math.min((u.right-u.left)/(2*p),(d.y-u.top)/h,(u.bottom-d.y)/h);a.strokeStyle="#00aeb8",a.beginPath(),a.moveTo(d.x,u.top),a.lineTo(d.x,u.bottom),a.stroke(),a.beginPath(),a.moveTo(u.left,u.bottom),a.lineTo(u.right,u.bottom),a.stroke(),Zn.length>1&&(a.strokeStyle="#ed35c5",a.lineWidth=2,a.beginPath(),Zn.forEach((M,y)=>{let C=d.x-M.lateral*g,A=d.y-M.forward*g;y?a.lineTo(C,A):a.moveTo(C,A)}),a.stroke());let x=fn,m=Q("world-map-odometry-position"),[f=0,S=0]=x?.position_m||[];m&&(m.textContent=`${f.toFixed(2)} m fwd \xB7 ${S.toFixed(2)} m left`),a.save(),a.translate(d.x-S*g,d.y-f*g),a.rotate(Number(x?.yaw_rad)||0),a.fillStyle="#00d6df",a.strokeStyle="#e8ffff",a.lineWidth=1,a.beginPath(),a.moveTo(0,-10),a.lineTo(7,8),a.lineTo(0,5),a.lineTo(-7,8),a.closePath(),a.fill(),a.stroke(),a.restore()}function Go(){if(xe){if(xe.resize(),at&&(at.material.uniforms.uViewportHeight.value=xe.renderer.domElement.height),yt?.classList.contains("is-camera-view")&&uh(),at&&(!Ec||!xe.camera.userData.userAdjusted)){at.geometry.boundingBox||at.geometry.computeBoundingBox();let i=at.geometry.boundingBox,e=i.getCenter(new D),t=i.getSize(new D),n=bt.degToRad(xe.camera.fov),r=2*Math.atan(Math.tan(n/2)*xe.camera.aspect),s=t.y/(2*Math.tan(n/2)),a=t.x/(2*Math.tan(r/2)),o=Math.max(s,a,.8)*.82+t.z*.18;xe.camera.userData.target=e,xe.camera.position.copy(e).add(new D(0,Math.max(.2,t.y*.1),o)),Ec=!0}xe.camera.lookAt(xe.camera.userData.target||new D),xe.render()}}function Rx(i){if(!xe||!at)return;if(i==="camera"){yt?.classList.add("is-camera-view"),xe.resize();let a=Vi(ut);xe.camera.fov=bt.radToDeg(2*Math.atan((ut?.height||480)/(2*a.fy))),xe.camera.userData.userAdjusted=!0;let o=Ts(),l=(Ic(_t)||new Gt).multiply(o.rotation),u=new D(0,0,-1).applyQuaternion(l);xe.camera.userData.target=o.position.clone().add(u),xe.camera.position.copy(o.position),xe.camera.up.set(0,1,0).applyQuaternion(l),xe.camera.lookAt(xe.camera.userData.target),uh(),Hi(),Es(),Kn();let d=Zt;d&&hh(d).then(async h=>Zt?.frame_id!==d.frame_id?!1:h?fh(h):(Xt&&(Xt.visible=!1),Kn(),!1)).then(()=>xe.render()).catch(h=>console.warn("Could not load camera-aligned 3D background:",h)),xe.render();return}yt?.classList.remove("is-camera-view"),xe.camera.fov=42,xe.resize(),at.geometry.boundingBox||at.geometry.computeBoundingBox();let e=at.geometry.boundingBox,t=e.getCenter(new D),n=e.getSize(new D),r=Math.max(n.x,n.y,n.z,2)*.95,s={top:new D(0,r,-.01),side:new D(r,Math.max(.2,n.y*.12),0),follow:new D(0,Math.max(.7,n.y*.24),r*.78)};xe.camera.userData.userAdjusted=!0,xe.camera.userData.target=t,xe.camera.position.copy(t).add(s[i]||s.follow),xe.camera.up.set(0,i==="top"?0:1,i==="top"?-1:0),xe.camera.lookAt(t),Hi(),Es(),Kn(),xe.render()}function Kn(){let i=!!(Yt?.available&&Number.isFinite(ut?.rawMin)),e=Q("world-map-cloud-hud-points"),t=Q("world-map-cloud-hud-depth"),n=Q("world-map-cloud-hud-age"),r=Q("world-map-cloud-hud-sync"),s=Q("world-map-cloud-hud-pipeline"),a=Q("world-map-cloud-hud-fps");e&&(e.textContent=`${Qu.toLocaleString()} points`),t&&(t.textContent=`MiDaS ${Zt?.latency_ms==null?"\u2014":`${Number(Zt.latency_ms).toFixed(1)} ms`}`);let o=Number(ut?.capturedAt)||0,c=o>0?Math.max(0,Date.now()/1e3-o):NaN;if(s){let M=Number(ut?.workerReceivedAt)||0,y=Number(ut?.publishedAt)||0,C=Number(ut?.browserFetchedAt)||0,A=Number(ut?.cloudBuiltAt)||0,I=Number(Zt?.inference_ms),N=(v,b)=>`${v} ${Number.isFinite(b)?`${Math.round(b)}ms`:"\u2014"}`;s.textContent=[N("pre",M&&o?Math.max(0,(M-o)*1e3):NaN),N("infer",I),N("svc",M&&y?Math.max(0,(y-M)*1e3):NaN),N("fetch",y&&C?Math.max(0,(C-y)*1e3):NaN),N("build",C&&A?Math.max(0,(A-C)*1e3):NaN)].join(" \xB7 "),s.title="pre: capture to worker acceptance; infer: model inference only; svc: service round-trip to publish; fetch: publish to browser; build: PNG decode and cloud upload."}let l=Number(kt?.captured_at),u=l>0&&o>0?Math.abs(l-o):NaN,d=!Number.isFinite(c)||c>.5||Number.isFinite(u)&&u>.5,h=Q("world-map-cloud-stale");if(h&&(h.hidden=!d,h.textContent=Number.isFinite(c)?c>.5?`STALE \xB7 MiDaS frame ${c.toFixed(1)} s old \xB7 last depth frame retained`:`STALE \xB7 camera/depth differ by ${u.toFixed(1)} s \xB7 detections hidden`:"MiDaS frame unavailable"),at?.material?.uniforms&&(at.material.uniforms.uOpacity.value=.92),n&&(n.textContent=Number.isFinite(c)?`Frame ${c.toFixed(1)} s`:"Frame \u2014"),r){let M=Number(kt?.captured_at),y=Number(ut?.capturedAt),C=M>0&&y>0?Math.abs(M-y):NaN,A=th===ut?.frameId?"camera matched":"depth view",I=String(ut?.frameId||"\u2014").slice(-14);r.textContent=Number.isFinite(C)?`D ${I} \xB7 camera \u0394 ${C.toFixed(1)} s \xB7 MiDaS cloud \xB7 ${A}`:`D ${I} \xB7 MiDaS cloud \xB7 ${A}`}let p=performance.now(),g=p-$u;a&&g>=500&&(a.textContent=`3D ${Math.round(Ac*1e3/g)} FPS`,Ac=0,$u=p);let x=Q("world-map-cloud-depth-caption"),f=Vi(ut).calibrated?"camera intrinsics calibrated":`camera FOV estimated ${ws.horizontalFovDeg}\xB0`;x&&(x.textContent=i?`Depth in metres \xB7 ${f}; radar remains independent`:`Pseudo-metres \xB7 uncalibrated; shape only, not range \xB7 ${f}`);let S=yt?.querySelector(".world-map-cloud-scale");S&&(S.hidden=!0),Bi&&(Bi.visible=!yt?.classList.contains("is-camera-view")),zi&&(zi.visible=!yt?.classList.contains("is-camera-view")),Xt&&(Xt.visible=!!yt?.classList.contains("is-camera-view"))}function vh(){if(!xe||!Bo||!yt||Bo.hidden)return;let i=yt.getBoundingClientRect();if(!i.width||!i.height)return;xe.camera.updateMatrixWorld();let e=[];for(let t of vs){let n=t.position.clone().project(xe.camera),r=t.element,s=n.z>=-1&&n.z<=1&&n.x>=-1.15&&n.x<=1.15&&n.y>=-1.15&&n.y<=1.15;if(r.hidden=!s,!s)continue;let a=bt.clamp((n.x+1)*i.width/2,8,i.width-8);if(t.marker){r.style.left=`${a}px`,r.style.top=`${bt.clamp((1-n.y)*i.height/2,10,i.height-10)}px`;continue}let o=Math.min(r.offsetWidth||150,i.width-16),c=r.offsetHeight||24;a=bt.clamp(a,o/2+8,i.width-o/2-8);let l=bt.clamp((1-n.y)*i.height/2-12,c+8,i.height-8),u=!1;for(let d=0;d<12;d++){let h=Math.ceil(d/2)*(c+5)*(d%2?-1:1),p=bt.clamp(l+h,c+8,i.height-8),g={left:a-o/2,top:p-c,right:a+o/2,bottom:p};if(!e.some(m=>g.left<m.right+4&&g.right>m.left-4&&g.top<m.bottom+3&&g.bottom>m.top-3)){e.push(g),r.style.left=`${a}px`,r.style.top=`${p}px`,u=!0;break}}r.hidden=!u}}function ko(i,e){vs=vs.filter(t=>t.layer!==i);for(let t of e){let n=document.createElement("span");n.className=t.marker?`world-map-cloud-radar-dot${t.motionClass?` ${t.motionClass}`:""}`:"world-map-cloud-object-label",n.textContent=t.text||"",Bo?.append(n),vs.push({...t,layer:i,element:n})}Bo?.querySelectorAll(".world-map-cloud-object-label,.world-map-cloud-radar-dot").forEach(t=>{vs.some(n=>n.element===t)||t.remove()}),vh()}function Hi(i=En,e=!1){if(!xe)return;let t=yt?.querySelector('[data-cloud-layer="radar"]')?.checked===!0,n=i?.targets||[],r=n.map(d=>{let h=d.position_m||d.position||[];return`${d.id||d.target_id||""}:${h[0]}:${h[1]}:${d.radial_speed_mps}`}).join("|"),s=`${t}:${i?.timestamp||"none"}:${r}:${yt?.classList.contains("is-camera-view")}`;if(!e&&s===Wu)return;Wu=s,bh(bs);let a=[];bs.visible=t;let o=Number(gi?.captured_at)||0,c=Number(i?.timestamp)||0,u=gi?.state==="ready"&&Date.now()/1e3-o<=.5&&Math.abs(o-c)<=.2?Pc(ah(gi),i,ut).map(d=>d.targetIndex):[];for(let[d,h]of n.entries()){let p=h.position_m||h.position||[],g=Number(p[0]),x=Number(p[1]);if(!Number.isFinite(g)||!Number.isFinite(x)||x<0||x>12)continue;let m=dh(new D(g,0,-x),i.timestamp);Vo(i.timestamp);let f=Number(fn?.captured_at)>0?Date.now()/1e3-Number(fn.captured_at):1/0,S=fn?.available&&f<=.35&&Number(fn.confidence)>=.35&&Number(fn.speed_mps)>=.05,M=Math.abs(Number(h.radial_speed_mps)||0)>=.05&&!S,y=S?"#9aa7ad":M?"#ed35c5":"#f2bc65",C=new dt(new di(.11,16,10),new Wt({color:y,transparent:!0,opacity:.24,depthTest:!1,depthWrite:!1}));C.position.copy(m),C.renderOrder=20,bs.add(C);let A=new dt(new di(.055,16,12),new Wt({color:y,depthTest:!1,depthWrite:!1}));A.position.copy(m),A.renderOrder=21,bs.add(A),a.push({position:m,marker:!0,motionClass:S?"is-ego-motion":M?"is-moving":""});let I=u.includes(d);a.push({position:m.clone().add(new D(0,.16,0)),text:`${I?"Person \xB7 YOLOX matched":`Radar target ${d+1} \xB7 unassociated`} \xB7 ${x.toFixed(1)} m forward${S?" \xB7 radial motion ego-uncompensated":""}`})}ko("radar",a),Rt==="3d"&&xe.render()}function Es(){if(!xe)return;bh(Ms);let i=yt?.querySelector('[data-cloud-layer="odometry"]')?.checked!==!1&&!yt?.classList.contains("is-camera-view");if(Ms.visible=i,Zn.length<2)return;let e=Ts().heightM,t=Zn.map(r=>new D(-r.lateral,e,-r.forward)),n=new Xn(new ft().setFromPoints(t),new nn({color:"#ed35c5",linewidth:2}));Ms.add(n),xe.render()}function bh(i){for(let e of[...i.children])i.remove(e),e.traverse?.(t=>{t.geometry?.dispose(),t.material?.dispose?.()})}async function Ix(i,e){let t=new Image;t.src=`data:${e};base64,${i}`,await t.decode();let n=document.createElement("canvas");n.width=t.naturalWidth,n.height=t.naturalHeight;let r=n.getContext("2d",{willReadFrequently:!0});return r.drawImage(t,0,0),{width:n.width,height:n.height,values:r.getImageData(0,0,n.width,n.height).data}}var Ku=new Map([[0,"#ef8354"],[3,"#00b4d8"],[5,"#9b5de5"],[12,"#ff4d6d"],[14,"#ff9f1c"],[15,"#ffd166"],[17,"#70e000"],[19,"#00f5d4"],[22,"#e76f51"],[27,"#4361ee"],[89,"#3a86ff"],[130,"#c77dff"],[141,"#fb5607"],[143,"#80ed99"]]);function ju(i){if(Ku.has(Number(i)))return new Be(Ku.get(Number(i)));let e=(Number(i)*137.508+18)%360;return new Be().setHSL(e/360,.72,.58)}function wh(i,e){if(!i?.available||!i.mask_png_base64)return!1;if(i.frame_id&&i.frame_id===e.frame_id)return!0;let t=Number(i.captured_at),n=Number(e.captured_at);return Number.isFinite(t)&&Number.isFinite(n)&&Math.abs(t-n)<=.25}async function Px(i,e=Rr){if(!xe||!i.depth_gray_jpeg_base64)return;let t=++gc,n=await ph(i);if(t!==gc||pt!=="sensors"||Rt!=="3d")return!1;ut=n,th="",Sc=wh(e,i)?String(e.frame_id||e.captured_at||""):"",Ss=null,_t=Number(i.captured_at)||0,Vo(_t),Tc+=1;let r=Yt;Kn();let s=Vi(n),a=Math.max(3,Math.ceil(Math.max(n.width,n.height)/120)),o=[],c=[];for(let d=0;d<n.height;d+=a)for(let h=0;h<n.width;h+=a){let p=(d*n.width+h)*4;if(ch(n,d*n.width+h)<.035)continue;let x=Cc(n,p,r),m=qt($t(h,d,x,s),Number(i.captured_at)||_t);o.push(m.x,m.y,m.z),c.push((n.normalizedValues?.[p]??n.values[p])/255)}let l=new ft;l.setAttribute("position",new nt(o,3)),l.setAttribute("depthValue",new nt(c,1)),l.computeBoundingBox(),Qu=o.length/3;let u=yt?.querySelector('[data-cloud-layer="cloud"]')?.checked!==!1;if(at){let d=at.geometry;at.geometry=l,at.visible=u,d.dispose()}else at=new Qr(l,yx(Number(Q("world-map-cloud-point-size")?.value||25)/1e3)),at.visible=u,xe.scene.add(at);return Hi(),Es(),Go(),xx(i).then(d=>{let h=ut;if(!d||pt!=="sensors"||Rt!=="3d"||!h)return;let p=Math.abs(Number(d.captured_at)-Number(h.capturedAt));if(h!==n&&(!Number.isFinite(p)||p>Do))return;let g={...d,frame_delta_s:p};Ss=g,Wo(h,g,Yt)}).catch(d=>console.warn("Could not pair YOLOX with MiDaS frame:",d)),yt?.classList.contains("is-camera-view")&&hh(i).then(d=>t===gc&&d?fh(d):!1).then(()=>xe.render()).catch(d=>console.warn("Could not load camera-aligned 3D background:",d)),n.cloudBuiltAt=Date.now()/1e3,Kn(),xe.render(),Cr=String(i.frame_id||""),!0}function Nx(i,e,t,n){let[r,s,a,o]=e.map(Number),c=/person|human/i.test(n);if(/tv|monitor|screen|television/i.test(n)){let f=Math.max(.015,(a-r)*.12),S=Math.max(.02,(o-s)*.12),M=Math.max(0,Math.floor((r-f)*i.width)),y=Math.min(i.width,Math.ceil((a+f)*i.width)),C=Math.max(0,Math.floor((s-S)*i.height)),A=Math.min(i.height,Math.ceil((o+S)*i.height)),I=Math.max(1,Math.floor(Math.min(y-M,A-C)/16)),N=[];for(let b=C;b<A;b+=I)for(let T=M;T<y;T+=I){let P=T/i.width,U=b/i.height;P>=r&&P<=a&&U>=s&&U<=o||N.push(Cc(i,(b*i.width+T)*4,t))}if(N.sort((b,T)=>b-T),!N.length)return null;let v=b=>N[Math.floor((N.length-1)*b)];return{near:v(.1),median:v(.5),far:v(.9),screen:!0}}let l=c?.25:.15,u=Math.max(0,Math.floor((r+(a-r)*l)*i.width)),d=Math.min(i.width,Math.ceil((a-(a-r)*l)*i.width)),h=Math.max(0,Math.floor((s+(o-s)*(c?.2:.15))*i.height)),p=Math.min(i.height,Math.ceil((s+(o-s)*(c?.72:.85))*i.height)),g=Math.max(1,Math.floor(Math.min(d-u,p-h)/12)),x=[];for(let f=h;f<p;f+=g)for(let S=u;S<d;S+=g)x.push(Cc(i,(f*i.width+S)*4,t));if(x.sort((f,S)=>f-S),!x.length)return null;let m=f=>x[Math.min(x.length-1,Math.floor((x.length-1)*f))];return{near:m(.1),median:m(.5),far:m(.9)}}function Wo(i,e,t=Yt){if(!xe||!i||Rt!=="3d")return;let n=yt?.querySelector('[data-cloud-layer="detections"]')?.checked!==!1,r=e?.frame_delta_s!=null&&Number.isFinite(Number(e.frame_delta_s))?Number(e.frame_delta_s):Math.abs(Number(e?.captured_at)-Number(i.capturedAt)),s=!!(i.frameId&&e?.frame_id===i.frameId)||Number.isFinite(r)&&r<=Do,a=n&&s&&e?.state==="ready"&&e?.paired!==!1?fx(e):[],o=`${n}:${Cr}:${e?.frame_id||""}:${a.length}:${Number(_t).toFixed(3)}`;if(o===Gu)return;Gu=o;let c=new Bt,l=[],u=["#55e7cc","#f2bc65","#e280ba","#77d69c"],d=!!(t?.available&&Number.isFinite(i.rawMin)&&Number.isFinite(i.rawMax)),h=s&&d&&r<=.15?sx(_t,.1):null,p=h?Pc(a,h,i):[];for(let[g,x]of a.entries()){let m=x.bbox;if(!Array.isArray(m)||m.length<4||!m.every(Pe=>Number.isFinite(Number(Pe))))continue;let[f,S,M,y]=m.map(Number),C=String(x.label||x.class_name||x.class||"object"),A=Nx(i,m,t,C);if(!A)continue;let I=p.find(Pe=>Pe.detection===x),N=s&&d?gx(A.median,t):null,v=I?I.forward:A.median,b=Math.max(0,A.far-A.near),T=d?Math.min(.6,Math.max(.15,v*.3)):Math.min(.35,Math.max(.02,v*.05)),P=A.screen?Math.min(b,d?.04:.02):Math.min(b,T),U=Math.max(.15,v-P/2),F=Math.max(U+(d?.03:.01),v+P/2),k=Vi(i),G=[qt($t(f*i.width,S*i.height,U,k),_t),qt($t(M*i.width,S*i.height,U,k),_t),qt($t(M*i.width,y*i.height,U,k),_t),qt($t(f*i.width,y*i.height,U,k),_t),qt($t(f*i.width,S*i.height,F,k),_t),qt($t(M*i.width,S*i.height,F,k),_t),qt($t(M*i.width,y*i.height,F,k),_t),qt($t(f*i.width,y*i.height,F,k),_t)],K=[0,1,1,2,2,3,3,0,4,5,5,6,6,7,7,4,0,4,1,5,2,6,3,7],W=new nn({color:u[g%u.length],depthTest:!1,transparent:!0,opacity:.95});c.add(new ci(new ft().setFromPoints(K.map(Pe=>G[Pe])),W));let se=qt($t((f+M)*i.width/2,S*i.height,U,k),_t),de=Math.round(Number(x.confidence??x.score??0)*100),Ae=I?`${I.forward.toFixed(2)} m \xB7 radar measured`:N?`${N.extrapolated?"~":""}${N.meters.toFixed(1)} m \xB7 MiDaS ${N.extrapolated?"extrapolated":"est."}`:s?`${A.median.toFixed(1)} pseudo-m \xB7 uncalibrated MiDaS`:"depth unpaired \xB7 relative shape only",fe=e?.frame_id!==i.frameId&&r>.15?` \xB7 YOLOX \u0394${r.toFixed(1)} s`:"",Oe=i.capturedAt>0?Math.max(0,Date.now()/1e3-i.capturedAt):1/0,$e=Oe>1.25?` \xB7 MiDaS stale ${Oe.toFixed(1)} s`:"";l.push({position:se,text:`${C} ${de}% \xB7 ${Ae}${fe}${$e}`})}mi&&(xe.scene.remove(mi),mi.traverse(g=>{g.geometry?.dispose(),g.material?.dispose?.()})),mi=c,mi.visible=n,xe.scene.add(mi),ko("detections",l),xe.render()}window.updateBodyWorldMap3D=i=>{ki=i,pt==="simulation"&&Rt==="3d"&&Ho(i)};var Gi=()=>document.visibilityState!=="hidden";setInterval(()=>{Gi()&&pt==="sensors"&&(Nc(),Dc())},100);setInterval(()=>{!Gi()||pt!=="sensors"||mh()},250);setInterval(()=>{Gi()&&Ex()},1500);setInterval(()=>{!Gi()||pt!=="sensors"||(gh(),xh(),_h())},500);setInterval(()=>{Gi()&&pt==="sensors"&&Tx()},1e3);setInterval(()=>{Gi()&&pt==="sensors"&&Ax()},500);document.addEventListener("visibilitychange",()=>{Gi()&&pt==="sensors"&&(Nc(),Dc(),mh(),gh(),xh(),_h())});ki&&Ho(ki);})();
/*! Bundled license information:

three/build/three.core.js:
three/build/three.module.js:
  (**
   * @license
   * Copyright 2010-2025 Three.js Authors
   * SPDX-License-Identifier: MIT
   *)
*/
