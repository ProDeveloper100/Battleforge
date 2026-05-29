""" 
    BATTLE FORGE - Cyberpunk Arcade Shooter v3.0  
"""
import pygame, sys, math, random, json, os, time

try:
    from noise import pnoise1
    HAVE_NOISE = True
except ImportError:
    HAVE_NOISE = False

SCREEN_W, SCREEN_H = 1280, 720
FPS      = 60
GRAVITY  = 0.55
TILE     = 48
CHUNK_W  = 20
SCORES_FILE = "neon_void_scores.json"

C = {
    "bg":(5,5,20),"cyan":(0,230,255),"pink":(255,0,180),
    "green":(0,255,120),"yellow":(255,230,0),"orange":(255,130,0),
    "white":(230,240,255),"dark":(10,10,35),"red":(255,40,60),
    "purple":(170,0,255),"teal":(0,200,180),"sky":(20,30,80),
    "gold":(255,200,0),
}

BIOMES = [
    {"name":"Neon City",          "bg":[(5,5,20),(8,5,30)],     "platform_col":(0,200,220),  "accent":C["cyan"],   "enemies":["bat","drone","tank"]},
    {"name":"Toxic Wasteland",    "bg":[(5,15,5),(8,25,5)],     "platform_col":(80,200,0),   "accent":C["green"],  "enemies":["bat","fish","tank"]},
    {"name":"Crimson Desert",     "bg":[(30,10,5),(50,15,5)],   "platform_col":(220,100,30), "accent":C["orange"], "enemies":["bat","drone","tank"]},
    {"name":"Frozen Void",        "bg":[(5,10,30),(10,20,50)],  "platform_col":(100,180,255),"accent":(150,220,255),"enemies":["bat","drone","fish"]},
    {"name":"Cyberpunk Industrial","bg":[(15,5,25),(25,5,40)],  "platform_col":(180,0,255),  "accent":C["purple"], "enemies":["drone","tank","bat"]},
    {"name":"Neon Jungle",        "bg":[(0,20,10),(0,35,15)],   "platform_col":(0,200,80),   "accent":C["teal"],   "enemies":["bat","fish","drone"]},
]

# ── Utilities ─────────────────────────────────────────────────────────────────
def lerp_color(a,b,t): return tuple(int(a[i]+(b[i]-a[i])*t) for i in range(3))
def clamp(v,lo,hi): return max(lo,min(hi,v))

def draw_glow(surf,color,pos,radius,alpha=80):
    if radius<1: return
    g=pygame.Surface((radius*2,radius*2),pygame.SRCALPHA)
    for r in range(radius,0,-max(1,radius//8)):
        a=int(alpha*(1-r/radius)**1.5)
        pygame.draw.circle(g,(*color[:3],a),(radius,radius),r)
    surf.blit(g,(pos[0]-radius,pos[1]-radius),special_flags=pygame.BLEND_RGBA_ADD)

def draw_neon_rect(surf,color,rect,width=2,glow_r=8):
    pygame.draw.rect(surf,color,rect,width,border_radius=4)
    g=pygame.Surface((rect[2]+glow_r*2,rect[3]+glow_r*2),pygame.SRCALPHA)
    for i in range(glow_r,0,-2):
        a=30-i*2
        if a>0:
            pygame.draw.rect(g,(*color[:3],a),(glow_r-i,glow_r-i,rect[2]+i*2,rect[3]+i*2),2,border_radius=4)
    surf.blit(g,(rect[0]-glow_r,rect[1]-glow_r),special_flags=pygame.BLEND_RGBA_ADD)

def neon_text(surf,font,text,color,center,glow=True):
    base=font.render(text,True,color)
    if glow:
        for d in range(6,0,-2):
            blur=font.render(text,True,tuple(min(255,c+40) for c in color[:3]))
            blur.set_alpha(30)
            surf.blit(blur,(center[0]-base.get_width()//2+d,center[1]-base.get_height()//2))
            surf.blit(blur,(center[0]-base.get_width()//2-d,center[1]-base.get_height()//2))
            surf.blit(blur,(center[0]-base.get_width()//2,center[1]-base.get_height()//2+d))
            surf.blit(blur,(center[0]-base.get_width()//2,center[1]-base.get_height()//2-d))
    surf.blit(base,(center[0]-base.get_width()//2,center[1]-base.get_height()//2))

# ── Perlin Noise ──────────────────────────────────────────────────────────────
class SimpleNoise:
    def __init__(self,seed=0):
        rng=random.Random(seed)
        self._grad=[rng.uniform(-1,1) for _ in range(512)]
    def __call__(self,x):
        ix=int(math.floor(x))&511; fx=x-math.floor(x)
        u=fx*fx*fx*(fx*(fx*6-15)+10)
        return (1-u)*self._grad[ix]*fx+u*self._grad[(ix+1)&511]*(fx-1)

_snoise=SimpleNoise(seed=42)

def perlin(x,octaves=4,persistence=0.5,lacunarity=2.0,scale=0.01):
    if HAVE_NOISE:
        return pnoise1(x*scale,octaves=octaves,persistence=persistence,lacunarity=lacunarity,repeat=9999999)
    val,amp,freq,norm=0.0,1.0,1.0,0.0
    for _ in range(octaves):
        val+=_snoise(x*scale*freq)*amp; norm+=amp; amp*=persistence; freq*=lacunarity
    return val/norm

# ── Sprite Factory ────────────────────────────────────────────────────────────
def make_player_sprite(color,facing=1,frame=0):
    """Detailed 40x56 cyberpunk soldier with helmet, jetpack, armour plates."""
    s=pygame.Surface((40,56),pygame.SRCALPHA)
    c=color
    dim=tuple(max(0,x-70) for x in c[:3])
    dark=tuple(max(0,x-130) for x in c[:3])
    hi=tuple(min(255,x+90) for x in c[:3])
    gold=C["yellow"]; red=C["red"]
    leg_bob=int(math.sin(frame*0.7)*5)

    # ── Boots ──
    pygame.draw.rect(s,dark,(5,46+leg_bob,10,10),border_radius=3)
    pygame.draw.rect(s,dark,(22,46-leg_bob,10,10),border_radius=3)
    # Boot toe plates
    pygame.draw.rect(s,c,(4,52+leg_bob,12,4),border_radius=2)
    pygame.draw.rect(s,c,(21,52-leg_bob,12,4),border_radius=2)
    # Boot trim lines
    pygame.draw.line(s,hi,(5,48+leg_bob),(14,48+leg_bob),1)
    pygame.draw.line(s,hi,(22,48-leg_bob),(31,48-leg_bob),1)

    # ── Legs with knee pads ──
    pygame.draw.rect(s,dim,(6,32+leg_bob,9,16))
    pygame.draw.rect(s,dim,(23,32-leg_bob,9,16))
    # Knee pads
    pygame.draw.rect(s,c,(5,36+leg_bob,11,7),border_radius=2)
    pygame.draw.rect(s,c,(22,36-leg_bob,11,7),border_radius=2)
    pygame.draw.rect(s,hi,(6,37+leg_bob,9,2))
    pygame.draw.rect(s,hi,(23,37-leg_bob,9,2))

    # ── Jetpack on back ──
    jp_x=2 if facing>=0 else 26
    pygame.draw.rect(s,dark,(jp_x,16,8,18),border_radius=3)
    pygame.draw.rect(s,dim,(jp_x,16,8,18),2,border_radius=3)
    # Jetpack exhaust
    exhaust=int(abs(math.sin(frame*0.5))*6)
    pygame.draw.rect(s,(255,100,0,180),(jp_x+1,34,3,exhaust),border_radius=1)
    pygame.draw.rect(s,(255,200,0,120),(jp_x+2,34,1,exhaust+2),border_radius=1)
    # Jetpack vents
    for vy in [19,24,29]:
        pygame.draw.rect(s,c,(jp_x+1,vy,6,2))

    # ── Body armour ──
    pygame.draw.rect(s,dim,(11,18,18,18),border_radius=4)
    pygame.draw.rect(s,c,(11,18,18,18),2,border_radius=4)
    # Chest armour plates
    pygame.draw.rect(s,dark,(13,20,7,8),border_radius=2)
    pygame.draw.rect(s,dark,(20,20,7,8),border_radius=2)
    pygame.draw.rect(s,dim,(13,20,7,8),1,border_radius=2)
    pygame.draw.rect(s,dim,(20,20,7,8),1,border_radius=2)
    # Chest light / core
    core_pulse=int(abs(math.sin(frame*0.12))*60)+160
    pygame.draw.rect(s,(0,core_pulse,core_pulse),(15,22,10,4),border_radius=2)
    # Waist belt
    pygame.draw.rect(s,dark,(11,33,18,4))
    pygame.draw.rect(s,gold,(11,33,18,2))
    # Belt buckle
    pygame.draw.rect(s,gold,(18,33,4,4),border_radius=1)

    # ── Shoulder pauldrons ──
    pygame.draw.rect(s,dim,(7,17,6,10),border_radius=3)
    pygame.draw.rect(s,c,(7,17,6,10),2,border_radius=3)
    pygame.draw.rect(s,dim,(27,17,6,10),border_radius=3)
    pygame.draw.rect(s,c,(27,17,6,10),2,border_radius=3)
    # Shoulder rivets
    pygame.draw.circle(s,hi,(10,21),2)
    pygame.draw.circle(s,hi,(30,21),2)

    # ── Helmet ──
    pygame.draw.rect(s,dim,(9,3,22,16),border_radius=6)
    pygame.draw.rect(s,c,(9,3,22,16),2,border_radius=6)
    # Helmet ridge
    pygame.draw.rect(s,hi,(18,3,4,3),border_radius=1)
    # Antenna
    pygame.draw.line(s,c,(20,3),(20,-4),2)
    pygame.draw.circle(s,C["cyan"],(20,-4),3)
    pulse_ant=int(abs(math.sin(frame*0.15))*150)+100
    draw_glow(s,C["cyan"],(20,-4),5,pulse_ant)
    # Ear pieces
    pygame.draw.rect(s,dark,(8,7,4,8),border_radius=2)
    pygame.draw.rect(s,c,(8,7,4,8),1,border_radius=2)
    pygame.draw.rect(s,dark,(28,7,4,8),border_radius=2)
    pygame.draw.rect(s,c,(28,7,4,8),1,border_radius=2)
    # Visor — wide glowing bar
    if facing>=0:
        pygame.draw.rect(s,(0,40,60),(15,8,16,6),border_radius=2)
        pygame.draw.rect(s,gold,(15,8,16,6),2,border_radius=2)
        pygame.draw.rect(s,(255,255,180,180),(16,9,8,2))
        # Scope on right
        pygame.draw.rect(s,dark,(29,9,4,4),border_radius=1)
        pygame.draw.circle(s,C["cyan"],(31,11),2)
    else:
        pygame.draw.rect(s,(0,40,60),(9,8,16,6),border_radius=2)
        pygame.draw.rect(s,gold,(9,8,16,6),2,border_radius=2)
        pygame.draw.rect(s,(255,255,180,180),(10,9,8,2))
        pygame.draw.rect(s,dark,(7,9,4,4),border_radius=1)
        pygame.draw.circle(s,C["cyan"],(9,11),2)

    # ── Gun arm ──
    if facing>=0:
        # Forearm
        pygame.draw.rect(s,dim,(28,22,8,6),border_radius=2)
        pygame.draw.rect(s,c,(28,22,8,6),1,border_radius=2)
        # Gun body
        pygame.draw.rect(s,dark,(33,20,10,9),border_radius=3)
        pygame.draw.rect(s,c,(33,20,10,9),2,border_radius=3)
        # Barrel
        pygame.draw.rect(s,c,(41,23,6,3))
        # Muzzle
        pygame.draw.circle(s,gold,(47,24),2)
        # Energy cell
        pygame.draw.rect(s,(0,200,255),(35,21,4,7),border_radius=1)
    else:
        pygame.draw.rect(s,dim,(4,22,8,6),border_radius=2)
        pygame.draw.rect(s,c,(4,22,8,6),1,border_radius=2)
        pygame.draw.rect(s,dark,(-3,20,10,9),border_radius=3)
        pygame.draw.rect(s,c,(-3,20,10,9),2,border_radius=3)
        pygame.draw.rect(s,c,(-9,23,6,3))
        pygame.draw.circle(s,gold,(-7,24),2)
        pygame.draw.rect(s,(0,200,255),(1,21,4,7),border_radius=1)

    # ── Overall glow ──
    draw_glow(s,c,(20,28),22,35)
    return s

def make_bat_sprite(frame=0):
    s=pygame.Surface((36,28),pygame.SRCALPHA); c=C["pink"]
    flap=int(math.sin(frame*0.3)*10)
    pygame.draw.polygon(s,(120,0,80),[(18,14),(0,14+flap),(6,4)])
    pygame.draw.polygon(s,(120,0,80),[(18,14),(36,14+flap),(30,4)])
    pygame.draw.polygon(s,c,[(18,14),(0,14+flap),(6,4)],1)
    pygame.draw.polygon(s,c,[(18,14),(36,14+flap),(30,4)],1)
    pygame.draw.ellipse(s,(160,0,100),(11,8,14,12)); pygame.draw.ellipse(s,c,(11,8,14,12),2)
    pygame.draw.circle(s,C["yellow"],(15,12),3); pygame.draw.circle(s,C["yellow"],(21,12),3)
    pygame.draw.circle(s,(0,0,0),(16,12),1); pygame.draw.circle(s,(0,0,0),(22,12),1)
    pygame.draw.polygon(s,(200,200,200),[(16,19),(14,23),(18,19)])
    pygame.draw.polygon(s,(200,200,200),[(20,19),(22,23),(18,19)])
    draw_glow(s,c,(18,14),14,60); return s

def make_fish_sprite(frame=0):
    s=pygame.Surface((40,26),pygame.SRCALPHA); c=C["teal"]
    tw=int(math.sin(frame*0.25)*4)
    pygame.draw.polygon(s,(0,120,100),[(8,13),(0,6+tw),(0,20+tw)])
    pygame.draw.polygon(s,c,[(8,13),(0,6+tw),(0,20+tw)],1)
    pygame.draw.ellipse(s,(0,150,130),(6,4,28,18)); pygame.draw.ellipse(s,c,(6,4,28,18),2)
    for i in range(3): pygame.draw.arc(s,c,(10+i*7,7,8,8),0,math.pi,1)
    pygame.draw.circle(s,C["yellow"],(30,11),4); pygame.draw.circle(s,(0,0,0),(31,11),2)
    pygame.draw.polygon(s,c,[(18,4),(22,0),(26,4)])
    draw_glow(s,c,(20,13),14,55); return s

def make_tank_sprite(frame=0):
    s=pygame.Surface((52,38),pygame.SRCALPHA); c=C["orange"]; dim=(120,60,0)
    pygame.draw.rect(s,(40,20,0),(2,28,48,10),border_radius=4)
    pygame.draw.rect(s,(80,40,0),(2,28,48,10),2,border_radius=4)
    for i in range(6): pygame.draw.line(s,c,(6+i*7,28),(6+i*7,38),1)
    for wx in [6,20,34,46]:
        pygame.draw.circle(s,dim,(wx,33),5); pygame.draw.circle(s,c,(wx,33),5,1)
    pygame.draw.rect(s,dim,(4,14,44,16),border_radius=3); pygame.draw.rect(s,c,(4,14,44,16),2,border_radius=3)
    pygame.draw.rect(s,(160,80,0),(8,16,12,12)); pygame.draw.rect(s,(160,80,0),(22,16,12,12))
    pygame.draw.rect(s,dim,(14,4,24,12),border_radius=4); pygame.draw.rect(s,c,(14,4,24,12),2,border_radius=4)
    pygame.draw.rect(s,c,(38,7,16,5)); pygame.draw.rect(s,dim,(39,8,14,3))
    draw_glow(s,c,(26,20),20,50); return s

def make_drone_sprite(frame=0):
    s=pygame.Surface((44,36),pygame.SRCALPHA); c=C["purple"]; rot=frame*0.12
    for a in [rot,rot+math.pi/2,rot+math.pi,rot+3*math.pi/2]:
        ex=22+int(math.cos(a)*16); ey=18+int(math.sin(a)*8)
        pygame.draw.line(s,(80,0,140),(22,18),(ex,ey),2)
        pygame.draw.circle(s,c,(ex,ey),5); pygame.draw.circle(s,(200,100,255),(ex,ey),3)
    pygame.draw.circle(s,(60,0,100),(22,18),12); pygame.draw.circle(s,c,(22,18),12,2)
    pygame.draw.circle(s,C["red"],(22,18),5); pygame.draw.circle(s,(255,80,80),(22,18),3)
    pygame.draw.circle(s,C["white"],(23,17),1); pygame.draw.circle(s,C["purple"],(22,26),3)
    draw_glow(s,c,(22,18),18,70); return s

def make_boss_sprite(frame=0,hp_frac=1.0):
    """Big 96x80 boss — a giant armoured cyber-mech."""
    s=pygame.Surface((96,80),pygame.SRCALPHA)
    c=lerp_color(C["red"],C["orange"],hp_frac)
    dim=tuple(max(0,x-80) for x in c[:3])
    # Legs
    leg=int(math.sin(frame*0.05)*6)
    pygame.draw.rect(s,dim,(10,60+leg,18,20),border_radius=3)
    pygame.draw.rect(s,dim,(68,60-leg,18,20),border_radius=3)
    pygame.draw.rect(s,c,(10,60+leg,18,4),border_radius=1)
    pygame.draw.rect(s,c,(68,60-leg,18,4),border_radius=1)
    # Body
    pygame.draw.rect(s,dim,(14,24,68,38),border_radius=6)
    pygame.draw.rect(s,c,(14,24,68,38),3,border_radius=6)
    # Chest pattern
    pygame.draw.rect(s,(255,50,50),(30,30,36,10),border_radius=3)
    pygame.draw.rect(s,c,(30,30,36,10),2,border_radius=3)
    # Shoulders / cannons
    pygame.draw.rect(s,dim,(0,22,16,24),border_radius=4)
    pygame.draw.rect(s,c,(0,22,16,24),2,border_radius=4)
    pygame.draw.rect(s,dim,(80,22,16,24),border_radius=4)
    pygame.draw.rect(s,c,(80,22,16,24),2,border_radius=4)
    # Gun barrels
    pygame.draw.rect(s,c,(-8,28,12,6)); pygame.draw.rect(s,c,(92,28,12,6))
    # Head
    pygame.draw.rect(s,dim,(24,4,48,22),border_radius=6)
    pygame.draw.rect(s,c,(24,4,48,22),2,border_radius=6)
    # Eyes — pulse red
    eye_pulse=int(abs(math.sin(frame*0.08))*200)+55
    pygame.draw.rect(s,(eye_pulse,0,0),(32,9,12,8),border_radius=3)
    pygame.draw.rect(s,(eye_pulse,0,0),(52,9,12,8),border_radius=3)
    pygame.draw.rect(s,(255,100,100),(34,11,6,4),border_radius=2)
    pygame.draw.rect(s,(255,100,100),(54,11,6,4),border_radius=2)
    draw_glow(s,c,(48,40),40,int(60*hp_frac)+20)
    return s

# ── Power-up ──────────────────────────────────────────────────────────────────
POWERUP_TYPES = [
    {"kind":"shield",     "color":C["cyan"],   "label":"SHIELD",      "duration":FPS*8},
    {"kind":"rapidfire",  "color":C["yellow"],  "label":"RAPID FIRE",  "duration":FPS*10},
    {"kind":"damage",     "color":C["orange"],  "label":"DOUBLE DMG",  "duration":FPS*10},
    {"kind":"speed",      "color":C["green"],   "label":"SPEED BOOST", "duration":FPS*8},
    {"kind":"health",     "color":C["pink"],    "label":"+2 HP",       "duration":0},
]

class PowerUp:
    W=28; H=28
    def __init__(self,x,y):
        kind_data=random.choice(POWERUP_TYPES)
        self.kind=kind_data["kind"]; self.color=kind_data["color"]
        self.label=kind_data["label"]; self.duration=kind_data["duration"]
        self.x=float(x); self.y=float(y); self.vy=0.0
        self.alive=True; self.tick=0
        self.rect=pygame.Rect(int(x),int(y),self.W,self.H)
    def update(self,platforms):
        self.tick+=1; self.vy+=GRAVITY*0.4
        self.y+=self.vy; self.rect.y=int(self.y)
        for p in platforms:
            if self.rect.colliderect(p.rect) and self.vy>0:
                self.y=p.rect.top-self.H; self.vy=0
                self.rect.y=int(self.y)
        if self.tick>FPS*12: self.alive=False
    def draw(self,surf,cam_x,cam_y):
        sx=int(self.x-cam_x); sy=int(self.y-cam_y)
        if sx<-40 or sx>SCREEN_W+40: return
        bob=int(math.sin(self.tick*0.1)*4)
        sy2=sy+bob
        # Hexagon shape
        cx2=sx+self.W//2; cy2=sy2+self.H//2
        pts=[(cx2+int(14*math.cos(math.pi/2+i*math.pi/3)),
              cy2+int(14*math.sin(math.pi/2+i*math.pi/3))) for i in range(6)]
        pygame.draw.polygon(surf,tuple(c//4 for c in self.color[:3]),pts)
        pygame.draw.polygon(surf,self.color,pts,2)
        draw_glow(surf,self.color,(cx2,cy2),18,80)
        # Icon letter
        font=pygame.font.Font(None,20)
        t=font.render(self.kind[0].upper(),True,self.color)
        surf.blit(t,(cx2-t.get_width()//2,cy2-t.get_height()//2))

# ── Boss ──────────────────────────────────────────────────────────────────────
class Boss:
    W=96; H=80
    def __init__(self,x,y,difficulty=1.0):
        self.x=float(x); self.y=float(y); self.vx=self.vy=0.0
        self.difficulty=difficulty
        self.max_hp=int(80*difficulty); self.hp=self.max_hp
        self.alive=True; self.frame=0; self.phase=0.0
        self.shoot_cd=0; self.hit_timer=0; self.score_val=2000
        self.rect=pygame.Rect(int(x),int(y),self.W,self.H)
        self.pattern=0; self.pattern_timer=0

    def update(self,px,py,platforms,bullets,particles):
        self.frame+=1; self.phase+=0.03; self.pattern_timer+=1
        spd=min(3.0,0.8+self.difficulty*0.2)

        # Switch attack patterns every 4 seconds
        if self.pattern_timer>FPS*4:
            self.pattern_timer=0; self.pattern=(self.pattern+1)%3

        if self.pattern==0:   # Chase
            dx=px-self.x; dy=py-self.y; dist=max(1,math.hypot(dx,dy))
            self.vx+=dx/dist*0.08*spd; self.vy+=dy/dist*0.08*spd
        elif self.pattern==1: # Strafe horizontally
            self.vx=math.sin(self.phase)*spd*2; self.vy+=GRAVITY*0.3
        else:                 # Hover above player
            tx=px; ty=py-160
            self.vx+=(tx-self.x)*0.02; self.vy+=(ty-self.y)*0.02

        self.vx=clamp(self.vx,-4,4); self.vy=clamp(self.vy,-6,6)
        self.vx*=0.92; self.vy*=0.92
        self.x+=self.vx; self.y+=self.vy
        self.rect.x=int(self.x); self.rect.y=int(self.y)

        # Platform landing
        for p in platforms:
            if self.rect.colliderect(p.rect) and self.vy>0:
                self.y=p.rect.top-self.H; self.vy=0
                self.rect.y=int(self.y)

        # Shoot at triple spread
        if self.shoot_cd<=0:
            dx=px-self.x; dy=py-self.y; dist=max(1,math.hypot(dx,dy))
            bspd=5+self.difficulty*0.5
            for spread in [-0.3,0,0.3]:
                ang=math.atan2(dy,dx)+spread
                bullets.append(Bullet(self.x+self.W//2,self.y+self.H//2,
                                      math.cos(ang)*bspd,math.sin(ang)*bspd,
                                      C["red"],"enemy",1))
            particles.emit(self.x+self.W//2,self.y+self.H//2,C["red"],8,4)
            self.shoot_cd=int(50/self.difficulty)
        if self.shoot_cd>0: self.shoot_cd-=1
        if self.hit_timer>0: self.hit_timer-=1
        if self.y>SCREEN_H+300: self.alive=False

    def hit(self,dmg,particles):
        self.hp-=dmg; self.hit_timer=8
        particles.emit(self.x+self.W//2,self.y+self.H//2,C["orange"],8,4)
        if self.hp<=0:
            self.alive=False
            particles.emit(self.x+self.W//2,self.y+self.H//2,C["red"],40,8,gravity=0.1,life=60)
            particles.emit(self.x+self.W//2,self.y+self.H//2,C["yellow"],20,6,life=45)
            particles.emit(self.x+self.W//2,self.y+self.H//2,C["white"],15,5,life=30)
            return True
        return False

    def draw(self,surf,cam_x,cam_y,tick):
        sx=int(self.x-cam_x); sy=int(self.y-cam_y)
        if sx>SCREEN_W+100 or sx<-100 or sy>SCREEN_H+100 or sy<-100: return
        hp_frac=max(0,self.hp/self.max_hp)
        spr=make_boss_sprite(self.frame,hp_frac)
        if self.hit_timer>0:
            wh=pygame.Surface(spr.get_size(),pygame.SRCALPHA); wh.fill((255,255,255,160))
            spr.blit(wh,(0,0),special_flags=pygame.BLEND_RGBA_ADD)
        surf.blit(spr,(sx,sy))
        # Boss HP bar — full width at top
        bar_x=sx; bar_y=sy-18; bar_w=self.W
        pygame.draw.rect(surf,(60,0,0),(bar_x,bar_y,bar_w,10))
        pygame.draw.rect(surf,lerp_color(C["red"],C["green"],hp_frac),(bar_x,bar_y,int(bar_w*hp_frac),10))
        pygame.draw.rect(surf,C["white"],(bar_x,bar_y,bar_w,10),1)

    def draw_hud_bar(self,surf,fonts):
        """Draw big boss HP bar at top center."""
        bw=500; bh=20; bx=SCREEN_W//2-bw//2; by=80
        hp_frac=max(0,self.hp/self.max_hp)
        pygame.draw.rect(surf,(40,0,0),(bx,by,bw,bh),border_radius=4)
        col=lerp_color(C["red"],C["orange"],hp_frac)
        pygame.draw.rect(surf,col,(bx,by,int(bw*hp_frac),bh),border_radius=4)
        draw_neon_rect(surf,C["red"],(bx,by,bw,bh),glow_r=6)
        neon_text(surf,fonts["small"],"BOSS",C["red"],(SCREEN_W//2,by-14))

#Particles 
class Particle:
    __slots__=("x","y","vx","vy","life","max_life","color","size","gravity","fade")
    def __init__(self,x,y,vx,vy,life,color,size=3,gravity=0,fade=True):
        self.x,self.y=x,y; self.vx,self.vy=vx,vy
        self.life=self.max_life=life; self.color=color
        self.size=size; self.gravity=gravity; self.fade=fade
    def update(self):
        self.vy+=self.gravity; self.x+=self.vx; self.y+=self.vy; self.vx*=0.95; self.life-=1
    def alive(self): return self.life>0
    def draw(self,surf,cx,cy):
        t=self.life/self.max_life; alpha=int(255*t) if self.fade else 255
        r=max(1,int(self.size*t)); sx,sy=int(self.x-cx),int(self.y-cy)
        if -r<sx<SCREEN_W+r and -r<sy<SCREEN_H+r:
            col=(*self.color[:3],alpha); s=pygame.Surface((r*2,r*2),pygame.SRCALPHA)
            pygame.draw.circle(s,col,(r,r),r)
            surf.blit(s,(sx-r,sy-r),special_flags=pygame.BLEND_RGBA_ADD)

class ParticleSystem:
    def __init__(self): self.particles=[]
    def emit(self,x,y,color,count=8,speed=4,size=4,gravity=0.1,fade=True,life=30):
        for _ in range(count):
            a=random.uniform(0,math.tau); spd=random.uniform(speed*0.3,speed)
            self.particles.append(Particle(x,y,math.cos(a)*spd,math.sin(a)*spd,
                                           random.randint(life//2,life),color,size,gravity,fade))
    def emit_dir(self,x,y,color,angle,spread=0.5,count=6,speed=5,size=3,life=20):
        for _ in range(count):
            a=angle+random.uniform(-spread,spread); spd=random.uniform(speed*0.5,speed)
            self.particles.append(Particle(x,y,math.cos(a)*spd,math.sin(a)*spd,life,color,size,0,True))
    def update(self):
        self.particles=[p for p in self.particles if p.alive()]
        for p in self.particles: p.update()
    def draw(self,surf,cx,cy):
        for p in self.particles: p.draw(surf,cx,cy)

# ── Damage Numbers ─────────────────────────────────────────────────────────────
class DamageNumber:
    def __init__(self,x,y,val,color):
        self.x=x; self.y=float(y); self.val=val; self.life=60; self.color=color
    def update(self): self.y-=1.2; self.life-=1
    def alive(self): return self.life>0
    def draw(self,surf,font,cx,cy):
        alpha=int(255*self.life/60)
        t=font.render(f"+{self.val}",True,self.color); t.set_alpha(alpha)
        surf.blit(t,(self.x-cx-t.get_width()//2,self.y-cy))

#Camera
class Camera:
    def __init__(self): self.x=self.y=self._tx=self._ty=0.0; self.shake=0
    def target(self,px,py): self._tx=px-SCREEN_W*0.35; self._ty=py-SCREEN_H*0.55
    def update(self):
        self.x+=(self._tx-self.x)*0.1; self.y+=(self._ty-self.y)*0.1
        if self.shake>0: self.shake-=1
    def shake_cam(self,n=8): self.shake=max(self.shake,n)
    def offset(self):
        sx=random.randint(-self.shake,self.shake) if self.shake else 0
        sy=random.randint(-self.shake,self.shake) if self.shake else 0
        return self.x+sx,self.y+sy

#World
class Platform:
    __slots__=("rect","biome_idx")
    def __init__(self,x,y,w,h,bi=0): self.rect=pygame.Rect(x,y,w,h); self.biome_idx=bi

class Chunk:
    def __init__(self,cx,world):
        self.cx=cx; self.platforms=[]; self.bg_stars=[]
        self.biome_idx=world.biome_at(cx*CHUNK_W); self._gen(world)
    def _gen(self,world):
        cx=self.cx; bx=cx*CHUNK_W
        self.platforms.append(Platform(bx*TILE,SCREEN_H+200,CHUNK_W*TILE,80,self.biome_idx))
        for i in range(CHUNK_W):
            tx=bx+i; raw=perlin(tx,octaves=3,scale=0.05)
            ty=SCREEN_H-120-int(raw*200)-60; ty=clamp(ty,SCREEN_H-420,SCREEN_H-80)
            if i%3==0:
                w=random.randint(3,7)*TILE
                self.platforms.append(Platform(tx*TILE,ty,w,16,self.biome_idx))
        rng=random.Random(cx*9999+1)
        for _ in range(40):
            self.bg_stars.append((rng.randint(bx*TILE,(bx+CHUNK_W)*TILE),rng.randint(0,SCREEN_H),
                                  rng.uniform(0.5,2.0),rng.choice([C["cyan"],C["pink"],C["purple"],(200,200,200)])))

class World:
    def __init__(self): self.chunks={}; self.biome_len=15
    def biome_at(self,tx): return ((tx//CHUNK_W)//self.biome_len)%len(BIOMES)
    def get_chunk(self,cx):
        if cx not in self.chunks: self.chunks[cx]=Chunk(cx,self)
        return self.chunks[cx]
    def get_platforms_near(self,cam_x):
        s=int(cam_x//(CHUNK_W*TILE))-1; e=s+4; plats=[]
        for cx in range(s,e+1): plats.extend(self.get_chunk(cx).platforms)
        for k in list(self.chunks):
            if k<s-3 or k>e+3: del self.chunks[k]
        return plats
    def get_stars_near(self,cam_x):
        s=int(cam_x//(CHUNK_W*TILE))-1; e=s+4; stars=[]
        for cx in range(s,e+1): stars.extend(self.get_chunk(cx).bg_stars)
        return stars
    def draw_bg(self,surf,cam_x,cam_y,bi):
        a,b=BIOMES[bi]["bg"]
        for y in range(SCREEN_H):
            col=lerp_color(a,b,y/SCREEN_H); pygame.draw.line(surf,col,(0,y),(SCREEN_W,y))
    def draw_stars(self,surf,stars,cam_x,cam_y):
        for sx,sy,sz,sc in stars:
            px=int(sx-cam_x*0.3)%SCREEN_W; py=int(sy-cam_y*0.1)%SCREEN_H
            r=max(1,int(sz)); pygame.draw.circle(surf,sc,(px,py),r)
            if sz>1.5: draw_glow(surf,sc,(px,py),r+4,50)
    def draw_platforms(self,surf,platforms,cam_x,cam_y,tick):
        for p in platforms:
            rx=p.rect.x-cam_x; ry=p.rect.y-cam_y
            if rx>SCREEN_W+TILE or rx<-TILE*CHUNK_W: continue
            col=BIOMES[p.biome_idx]["platform_col"]; acc=BIOMES[p.biome_idx]["accent"]
            pygame.draw.rect(surf,tuple(c//3 for c in col),(rx,ry,p.rect.w,p.rect.h))
            pygame.draw.rect(surf,col,(rx,ry,p.rect.w,3))
            pulse=0.5+0.5*math.sin(tick*0.05+p.rect.x*0.003)
            draw_glow(surf,acc,(rx+p.rect.w//2,ry+2),int(12*pulse)+4,30)

#Bullet
class Bullet:
    def __init__(self,x,y,vx,vy,color,owner="player",damage=1):
        self.x=float(x); self.y=float(y); self.vx=float(vx); self.vy=float(vy)
        self.color=color; self.owner=owner; self.damage=damage; self.alive=True; self.trail=[]
    def update(self):
        self.trail.append((self.x,self.y))
        if len(self.trail)>8: self.trail.pop(0)
        self.x+=self.vx; self.y+=self.vy
        if self.owner=="enemy":
            if not hasattr(self,"dist_travelled"): self.dist_travelled=0
            self.dist_travelled+=math.hypot(self.vx,self.vy)
            if self.dist_travelled>400: self.alive=False
        if self.x<-200 or self.x>999999 or self.y<-500 or self.y>SCREEN_H+500:
            self.alive=False
    def draw(self,surf,cx,cy):
        for i,(tx,ty) in enumerate(self.trail):
            t=i/len(self.trail); alpha=int(180*t); r=max(1,int(3*t))
            s=pygame.Surface((r*2+1,r*2+1),pygame.SRCALPHA)
            pygame.draw.circle(s,(*self.color[:3],alpha),(r,r),r)
            surf.blit(s,(tx-cx-r,ty-cy-r),special_flags=pygame.BLEND_RGBA_ADD)
        bx,by=int(self.x-cx),int(self.y-cy)
        if -10<bx<SCREEN_W+10 and -10<by<SCREEN_H+10:
            pygame.draw.circle(surf,self.color,(bx,by),4)
            draw_glow(surf,self.color,(bx,by),10,100)

#Enemy
class Enemy:
    def __init__(self,x,y,kind,difficulty=1.0):
        self.x=float(x); self.y=float(y); self.vx=self.vy=0.0
        self.kind=kind; self.difficulty=difficulty; self.alive=True
        self.hit_timer=0; self.shoot_cd=0; self.phase=random.uniform(0,math.tau)
        self.frame=0; self._setup(kind,difficulty)
    def _setup(self,kind,diff):
        if kind=="bat":   self.hp=self.max_hp=max(1,int(2*diff)); self.color=C["pink"];   self.w=self.h=36; self.score_val=50
        elif kind=="fish":self.hp=self.max_hp=max(1,int(3*diff)); self.color=C["teal"];   self.w=40;self.h=26;self.score_val=70
        elif kind=="tank":self.hp=self.max_hp=max(2,int(8*diff)); self.color=C["orange"]; self.w=52;self.h=38;self.score_val=200
        elif kind=="drone":self.hp=self.max_hp=max(1,int(3*diff));self.color=C["purple"]; self.w=self.h=44;self.score_val=100
        else: self.hp=self.max_hp=1; self.color=C["white"]; self.w=self.h=24; self.score_val=30
        self.rect=pygame.Rect(int(self.x),int(self.y),self.w,self.h)
    def update(self,px,py,platforms,bullets,particles,diff):
        spd=min(4.0,0.8+diff*0.25); self.phase+=0.05; self.frame+=1
        if self.kind=="bat":
            dx=px-self.x; dy=py-self.y; dist=math.hypot(dx,dy)
            if dist>0: self.vx+=dx/dist*0.12*spd; self.vy+=dy/dist*0.12*spd
            self.vx*=0.9; self.vy*=0.9; self.vy+=math.sin(self.phase)*0.25
        elif self.kind=="fish":
            self.vx=math.cos(self.phase*0.3)*spd*1.2; self.vy+=GRAVITY*0.5
            for p in platforms:
                if self.rect.colliderect(p.rect): self.vy=-random.uniform(7,10)*spd
        elif self.kind=="tank":
            dx=px-self.x; self.vx+=(.05 if dx>0 else -.05)*spd; self.vx=clamp(self.vx,-1.2,1.2)
            self.vy+=GRAVITY
            for p in platforms:
                if self.rect.colliderect(p.rect): self.vy=0; self.y=p.rect.top-self.h
            if self.shoot_cd<=0 and abs(px-self.x)<600:
                dx2=px-self.x; dy2=py-self.y; dist2=max(1,math.hypot(dx2,dy2))
                bullets.append(Bullet(self.x+self.w//2,self.y+self.h//2,dx2/dist2*(4+diff*0.5),dy2/dist2*(4+diff*0.5),C["orange"],"enemy",1))
                self.shoot_cd=int(100/diff); particles.emit(self.x+self.w//2,self.y+self.h//2,C["orange"],6,3)
            if self.shoot_cd>0: self.shoot_cd-=1
        elif self.kind=="drone":
            self.vx=-spd*1.8; self.vy=math.sin(self.phase*0.5)*2
            if self.shoot_cd<=0 and abs(px-self.x)<500:
                dx2=px-self.x; dy2=py-self.y; dist2=max(1,math.hypot(dx2,dy2))
                bullets.append(Bullet(self.x+self.w//2,self.y+self.h//2,dx2/dist2*3.5,dy2/dist2*3.5,C["purple"],"enemy",1))
                self.shoot_cd=int(70/diff); particles.emit(self.x+self.w//2,self.y+self.h//2,C["purple"],4,2)
            if self.shoot_cd>0: self.shoot_cd-=1
        self.x+=self.vx; self.y+=self.vy
        self.rect.x=int(self.x); self.rect.y=int(self.y)
        if self.hit_timer>0: self.hit_timer-=1
        if self.y>SCREEN_H+400: self.alive=False
    def hit(self,dmg,particles):
        self.hp-=dmg; self.hit_timer=10
        particles.emit(self.x+self.w//2,self.y+self.h//2,self.color,10,4)
        if self.hp<=0:
            self.alive=False
            particles.emit(self.x+self.w//2,self.y+self.h//2,self.color,25,7,gravity=0.1,life=45)
            particles.emit(self.x+self.w//2,self.y+self.h//2,C["white"],10,5,gravity=0.05,life=30)
            return True
        return False
    def draw(self,surf,cam_x,cam_y,tick):
        sx=int(self.x-cam_x); sy=int(self.y-cam_y)
        if sx>SCREEN_W+60 or sx<-80 or sy>SCREEN_H+60 or sy<-80: return
        if self.kind=="bat": spr=make_bat_sprite(self.frame)
        elif self.kind=="fish": spr=make_fish_sprite(self.frame)
        elif self.kind=="tank": spr=make_tank_sprite(self.frame)
        elif self.kind=="drone": spr=make_drone_sprite(self.frame)
        else:
            spr=pygame.Surface((self.w,self.h),pygame.SRCALPHA)
            pygame.draw.rect(spr,self.color,(0,0,self.w,self.h))
        if self.hit_timer>0:
            wh=pygame.Surface(spr.get_size(),pygame.SRCALPHA); wh.fill((255,255,255,160))
            spr.blit(wh,(0,0),special_flags=pygame.BLEND_RGBA_ADD)
        surf.blit(spr,(sx,sy))
        if self.hp<self.max_hp:
            frac=self.hp/self.max_hp
            pygame.draw.rect(surf,(60,0,0),(sx,sy-10,self.w,5))
            pygame.draw.rect(surf,C["red"],(sx,sy-10,int(self.w*frac),5))

#Player
class Player:
    W,H=40,56; JUMP_VEL=-13.5; MOVE_SPD=5.5; SHOOT_CD=10; INVINCIBLE=90; MAX_HP=10
    def __init__(self,x,y):
        self.x=float(x); self.y=float(y); self.vx=self.vy=0.0
        self.on_ground=False; self.jumps_left=2; self.hp=self.MAX_HP
        self.alive=True; self.shoot_cd=0; self.invincible=0; self.facing=1
        self.hit_timer=0; self.score=0; self.frame=0; self.frame_tick=0
        self.rect=pygame.Rect(int(x),int(y),self.W,self.H); self.death_timer=0
        # Power-up states
        self.shield=0; self.rapidfire=0; self.damage_boost=0; self.speed_boost=0
        self.active_powerups={}  # kind -> timer

    def apply_powerup(self,pu):
        if pu.kind=="health":
            self.hp=min(self.MAX_HP,self.hp+2)
        else:
            self.active_powerups[pu.kind]=pu.duration

    @property
    def shoot_cooldown(self): return 5 if "rapidfire" in self.active_powerups else self.SHOOT_CD
    @property
    def bullet_damage(self): return 2 if "damage" in self.active_powerups else 1
    @property
    def move_spd(self): return 7.5 if "speed" in self.active_powerups else self.MOVE_SPD
    @property
    def has_shield(self): return "shield" in self.active_powerups

    def update_powerups(self):
        expired=[k for k,v in self.active_powerups.items() if v<=0]
        for k in expired: del self.active_powerups[k]
        for k in self.active_powerups: self.active_powerups[k]-=1

    def shoot(self,mx,my,cam_x,cam_y,bullets,particles):
        if self.shoot_cd>0 or not self.alive: return
        wx=self.x+self.W//2; wy=self.y+self.H//2
        tx=mx+cam_x; ty=my+cam_y; dx=tx-wx; dy=ty-wy
        dist=max(1,math.hypot(dx,dy)); spd=16
        col=C["orange"] if self.bullet_damage>1 else C["cyan"]
        bullets.append(Bullet(wx,wy,dx/dist*spd,dy/dist*spd,col,"player",self.bullet_damage))
        particles.emit_dir(wx,wy,col,math.atan2(dy,dx),spread=0.3,count=5,speed=4,life=15)
        self.shoot_cd=self.shoot_cooldown; self.facing=1 if dx>=0 else -1

    def take_damage(self,dmg,cam,particles):
        if self.invincible>0 or not self.alive: return
        if self.has_shield:
            del self.active_powerups["shield"]
            particles.emit(self.x+self.W//2,self.y+self.H//2,C["cyan"],15,6)
            cam.shake_cam(5); self.invincible=30; return
        self.hp-=dmg; self.invincible=self.INVINCIBLE; self.hit_timer=20
        cam.shake_cam(10); particles.emit(self.x+self.W//2,self.y+self.H//2,C["red"],12,5,gravity=0.1)
        if self.hp<=0: self.hp=0; self.alive=False; self.death_timer=120

    def update(self,keys,platforms):
        self.update_powerups()
        if not self.alive: self.death_timer-=1; return
        moving=False
        if keys[pygame.K_a] or keys[pygame.K_LEFT]: self.vx-=1.5; self.facing=-1; moving=True
        if keys[pygame.K_d] or keys[pygame.K_RIGHT]: self.vx+=1.5; self.facing=1; moving=True
        self.vx=clamp(self.vx,-self.move_spd,self.move_spd)
        self.vx*=0.78 if self.on_ground else 0.88
        self.vy+=GRAVITY; self.vy=clamp(self.vy,-20,25)
        self.x+=self.vx; self.y+=self.vy
        self.rect.x=int(self.x); self.rect.y=int(self.y); self.on_ground=False
        for p in platforms:
            if self.rect.colliderect(p.rect):
                if self.vy>=0 and self.rect.bottom-p.rect.top<20:
                    self.y=p.rect.top-self.H; self.vy=0; self.on_ground=True; self.jumps_left=2
                elif self.vy<0 and self.rect.top-p.rect.bottom>-12:
                    self.y=float(p.rect.bottom); self.vy=1
                else:
                    self.x=p.rect.left-self.W if self.vx>0 else float(p.rect.right); self.vx=0
                self.rect.x=int(self.x); self.rect.y=int(self.y)
        if self.shoot_cd>0: self.shoot_cd-=1
        if self.invincible>0: self.invincible-=1
        if self.hit_timer>0: self.hit_timer-=1
        if moving and self.on_ground:
            self.frame_tick+=1
            if self.frame_tick%6==0: self.frame=(self.frame+1)%8
        elif not moving: self.frame=0
        if self.y>SCREEN_H+300: self.take_damage(99,Camera(),ParticleSystem())

    def jump(self):
        if not self.alive: return
        if self.jumps_left>0:
            self.vy=self.JUMP_VEL*(1.0 if self.jumps_left==2 else 0.8); self.jumps_left-=1

    def draw(self,surf,cam_x,cam_y,tick):
        sx=int(self.x-cam_x); sy=int(self.y-cam_y)
        if not self.alive:
            if self.death_timer>0:
                t=self.death_timer/120; r=int((1-t)*60)
                col=lerp_color(C["red"],C["yellow"],t)
                draw_glow(surf,col,(sx+self.W//2,sy+self.H//2),r,int(150*t))
            return
        if self.invincible>0 and (self.invincible//4)%2==1: return
        col=C["red"] if self.hit_timer>0 else C["cyan"]
        spr=make_player_sprite(col,self.facing,self.frame)
        if self.facing<0: spr=pygame.transform.flip(spr,True,False)
        surf.blit(spr,(sx,sy))
        # Shield bubble
        if self.has_shield:
            t2=pygame.time.get_ticks()//10
            shield_alpha=int(80+40*math.sin(t2*0.1))
            draw_glow(surf,C["cyan"],(sx+self.W//2,sy+self.H//2),32,shield_alpha)
        draw_glow(surf,col,(sx+self.W//2,sy+self.H//2),16,40)

    def draw_hp(self,surf,font):
        for i in range(self.MAX_HP):
            col=C["cyan"] if i<self.hp else (40,40,60)
            x=20+i*26; pygame.draw.rect(surf,col,(x,16,18,18),border_radius=3)
            if i<self.hp: draw_glow(surf,col,(x+9,25),12,60)

    def draw_powerup_bar(self,surf,fonts):
        x=20; y=SCREEN_H-40
        for kind,timer in self.active_powerups.items():
            pd=next((p for p in POWERUP_TYPES if p["kind"]==kind),None)
            if not pd: continue
            col=pd["color"]; label=pd["label"]
            frac=timer/pd["duration"] if pd["duration"]>0 else 1.0
            bw=120
            pygame.draw.rect(surf,(30,30,50),(x,y,bw,18),border_radius=4)
            pygame.draw.rect(surf,col,(x,y,int(bw*frac),18),border_radius=4)
            draw_neon_rect(surf,col,(x,y,bw,18),glow_r=4)
            lt=fonts["small"].render(label,True,col); lt.set_alpha(220)
            surf.blit(lt,(x+4,y+1)); x+=bw+12

#Spawner
class Spawner:
    def __init__(self): self.timer=0; self.interval=180; self.boss_timer=0
    def update(self,enemies,bosses,powerups,px,py,world,cam_x,difficulty,platforms):
        self.timer+=1; self.boss_timer+=1
        self.interval=max(40,180-int(difficulty*15))
        if self.timer>=self.interval:
            self.timer=0
            bi=world.biome_at(int((px+SCREEN_W)//TILE))
            pool=BIOMES[bi]["enemies"]; kind=random.choice(pool)
            ex=cam_x+SCREEN_W+random.randint(50,200)
            ey=py+random.randint(-200,0)
            enemies.append(Enemy(ex,ey,kind,difficulty))
            if difficulty>2.5 and random.random()<0.35:
                enemies.append(Enemy(ex,py-random.randint(100,300),random.choice(pool),difficulty))
        # Boss every 90 seconds, max 1 on screen
        if self.boss_timer>=FPS*40 and len(bosses)==0:
            self.boss_timer=0
            ex=cam_x+SCREEN_W+100
            bosses.append(Boss(ex,py-200,difficulty))
        # Power-up drops randomly
        if random.random()<0.002 and len(powerups)<4:
            ex=cam_x+random.randint(100,SCREEN_W-100)
            ey=py-random.randint(50,200)
            powerups.append(PowerUp(ex,ey))

#Score helpers
def load_scores():
    if os.path.exists(SCORES_FILE):
        try:
            with open(SCORES_FILE,"r") as f: return json.load(f)
        except: pass
    return []

def save_scores(scores):
    best={}
    for e in scores:
        u=e["username"]
        if u not in best or e["score"]>best[u]["score"]: best[u]=e
    result=sorted(best.values(),key=lambda e:e["score"],reverse=True)[:20]
    with open(SCORES_FILE,"w") as f: json.dump(result,f)
    return result

def add_score(scores,username,score):
    scores.append({"username":username,"score":score,"time":int(time.time())})
    return save_scores(scores)

#UI Helpers
class NeonButton:
    def __init__(self,x,y,w,h,text,color=None):
        self.rect=pygame.Rect(x-w//2,y-h//2,w,h)
        self.text=text; self.color=color or C["cyan"]; self.hover=False
    def check(self,mpos): self.hover=self.rect.collidepoint(mpos)
    def draw(self,surf,font):
        col=tuple(min(255,c+60) for c in self.color[:3]) if self.hover else self.color
        bg=tuple(c//5 for c in col[:3])
        pygame.draw.rect(surf,bg,self.rect,border_radius=10)
        draw_neon_rect(surf,col,self.rect,width=2,glow_r=12)
        pygame.draw.rect(surf,col,(self.rect.x,self.rect.y+6,4,self.rect.h-12))
        pygame.draw.rect(surf,col,(self.rect.right-4,self.rect.y+6,4,self.rect.h-12))
        neon_text(surf,font,self.text,col,(self.rect.centerx,self.rect.centery))
    def clicked(self,event):
        return event.type==pygame.MOUSEBUTTONDOWN and event.button==1 and self.rect.collidepoint(event.pos)

class InputBox:
    def __init__(self,x,y,w,h,placeholder=""):
        self.rect=pygame.Rect(x-w//2,y-h//2,w,h); self.text=""; self.placeholder=placeholder
    def handle(self,event):
        if event.type==pygame.KEYDOWN:
            if event.key==pygame.K_BACKSPACE: self.text=self.text[:-1]
            elif event.key not in (pygame.K_RETURN,pygame.K_ESCAPE):
                if len(self.text)<16: self.text+=event.unicode
    def draw(self,surf,font):
        col=C["cyan"]; pygame.draw.rect(surf,(10,10,30),self.rect,border_radius=6)
        draw_neon_rect(surf,col,self.rect,glow_r=8)
        txt=self.text if self.text else self.placeholder
        c=col if self.text else (80,80,120)
        t=font.render(txt,True,c)
        surf.blit(t,(self.rect.x+10,self.rect.centery-t.get_height()//2))
        if self.text and (pygame.time.get_ticks()//500)%2==0:
            cx2=self.rect.x+10+t.get_width()+2
            pygame.draw.line(surf,col,(cx2,self.rect.centery-12),(cx2,self.rect.centery+12),2)

#Background helpers
def _draw_scanlines(surf):
    sl=pygame.Surface((SCREEN_W,SCREEN_H),pygame.SRCALPHA)
    for y in range(0,SCREEN_H,4): pygame.draw.line(sl,(0,0,0,25),(0,y),(SCREEN_W,y))
    surf.blit(sl,(0,0))

def _draw_grid(surf,tick):
    s=pygame.Surface((SCREEN_W,SCREEN_H),pygame.SRCALPHA)
    offset=(tick*0.5)%60
    for x in range(0,SCREEN_W,60): pygame.draw.line(s,(0,200,255,10),(x,0),(x,SCREEN_H))
    for y in range(0,SCREEN_H,60): pygame.draw.line(s,(0,200,255,10),(0,int(y+offset)),(SCREEN_W,int(y+offset)))
    surf.blit(s,(0,0))

def _draw_city_bg(surf,tick):
    """Animated city background used on login + menu screens."""
    city_surf=pygame.Surface((SCREEN_W,SCREEN_H),pygame.SRCALPHA)
    buildings=[
        (0,420,55,300),(60,380,75,340),(140,340,90,380),(235,400,45,320),
        (285,310,110,410),(400,370,65,350),(470,290,130,430),(605,370,55,350),
        (665,320,85,400),(755,390,50,330),(810,340,100,380),(915,380,65,340),
        (985,300,75,420),(1065,350,120,370),(1190,360,90,360),
    ]
    for (bx,by,bw,bh) in buildings:
        rbx=bx-int(tick*0.3)%60
        pygame.draw.rect(city_surf,(12,12,35,220),(rbx,by,bw,bh))
        pygame.draw.rect(city_surf,(0,180,200,80),(rbx,by,bw,3))
        for wy2 in range(by+18,by+bh-18,20):
            for wx2 in range(rbx+7,rbx+bw-7,13):
                rng2=random.Random(bx*77+wy2+wx2)
                if rng2.random()>0.45:
                    wc=rng2.choice([C["cyan"],C["yellow"],C["pink"],C["purple"]])
                    walpha=40 if rng2.random()>0.97 else 160
                    pygame.draw.rect(city_surf,(*wc,walpha),(wx2,wy2,5,7))
    surf.blit(city_surf,(0,0))
    # Rising neon particles
    for i in range(12):
        px2=int((SCREEN_W//12)*i+math.sin(tick*0.03+i)*40)
        py2=int(SCREEN_H-((tick*0.8+i*80)%SCREEN_H))
        col2=[C["cyan"],C["pink"],C["purple"],C["teal"]][i%4]
        r2=max(1,int(2+math.sin(tick*0.05+i)*1.5))
        pygame.draw.circle(surf,col2,(px2,py2),r2)
        draw_glow(surf,col2,(px2,py2),r2+6,30)
    # Sweep line
    scan_y=int((tick*2)%SCREEN_H)
    sc=pygame.Surface((SCREEN_W,3),pygame.SRCALPHA); sc.fill((*C["cyan"],35))
    surf.blit(sc,(0,scan_y))

#Intro
class IntroSequence:
    DURATION=FPS*6
    def __init__(self,fonts):
        self.fonts=fonts; self.tick=0; self.done=False
        self.particles=ParticleSystem(); self.bolts=[]; self.bolt_timer=0
    def handle(self,event):
        if event.type in (pygame.KEYDOWN,pygame.MOUSEBUTTONDOWN): self.done=True
    def update(self):
        self.tick+=1; self.bolt_timer+=1
        if self.bolt_timer>8:
            self.bolt_timer=0
            self.bolts=[(random.randint(0,SCREEN_W),random.randint(0,SCREEN_H//3),
                         random.randint(0,SCREEN_W),random.randint(SCREEN_H//2,SCREEN_H))
                        for _ in range(random.randint(3,8))]
        if self.tick%3==0:
            self.particles.emit(random.randint(0,SCREEN_W),SCREEN_H,
                                random.choice([C["cyan"],C["pink"],C["purple"]]),
                                count=2,speed=random.uniform(1,4),size=3,gravity=-0.05,life=90)
        self.particles.update()
        if self.tick>=self.DURATION: self.done=True
    def draw(self,surf):
        t=min(self.tick/self.DURATION,1.0)
        surf.fill((0,0,0)); _draw_grid(surf,self.tick*2)
        if t>0.15:
            city_alpha=int(clamp((t-0.15)*5,0,1)*200)
            cs=pygame.Surface((SCREEN_W,SCREEN_H),pygame.SRCALPHA)
            for (bx,by,bw,bh) in [(0,380,60,340),(65,340,80,360),(150,300,100,420),(255,360,50,360),
                                    (310,280,120,440),(435,350,70,370),(510,260,140,460),(655,340,60,380),
                                    (720,290,90,430),(815,360,55,360),(875,310,110,410),(990,350,70,370),
                                    (1065,280,80,440),(1150,320,130,400)]:
                pygame.draw.rect(cs,(15,15,40,city_alpha),(bx,by,bw,bh))
                for wy2 in range(by+20,by+bh-20,22):
                    for wx2 in range(bx+8,bx+bw-8,14):
                        if random.Random(bx*100+wy2+wx2).random()>0.4:
                            wc=random.Random(bx+wy2).choice([C["cyan"],C["yellow"],C["pink"]])
                            pygame.draw.rect(cs,(*wc,city_alpha),(wx2,wy2,6,8))
            surf.blit(cs,(0,0))
        self.particles.draw(surf,0,0)
        if 0.1<t<0.7:
            ba=int(clamp(math.sin(self.tick*0.4)*200,0,180))
            if ba>60:
                for (x1,y1,x2,y2) in self.bolts[:3]:
                    pts=[(x1,y1)]
                    for _ in range(6): pts.append((pts[-1][0]+random.randint(-40,40),pts[-1][1]+random.randint(30,80)))
                    pts.append((x2,y2))
                    ls=pygame.Surface((SCREEN_W,SCREEN_H),pygame.SRCALPHA)
                    pygame.draw.lines(ls,(*C["cyan"],ba),False,pts,2)
                    surf.blit(ls,(0,0),special_flags=pygame.BLEND_RGBA_ADD)
        if t>0.2:
            alpha_t=int(clamp((t-0.2)*5,0,1)*255)
            ts=self.fonts["big"].render("BATTLE FORGE",True,C["cyan"]); ts.set_alpha(alpha_t)
            surf.blit(ts,(SCREEN_W//2-ts.get_width()//2,SCREEN_H//2-120))
            la=int(clamp((t-0.2)*5,0,1)*180)
            ls=pygame.Surface((500,2),pygame.SRCALPHA); ls.fill((*C["cyan"],la)); surf.blit(ls,(SCREEN_W//2-250,SCREEN_H//2-82))
            ls2=pygame.Surface((300,1),pygame.SRCALPHA); ls2.fill((*C["pink"],la)); surf.blit(ls2,(SCREEN_W//2-150,SCREEN_H//2-78))
        if t>0.38:
            sa=int(clamp((t-0.38)*6,0,1)*255)
            sub=self.fonts["med"].render("C Y B E R P U N K   A R C A D E   S U R V I V O R",True,C["pink"]); sub.set_alpha(sa)
            surf.blit(sub,(SCREEN_W//2-sub.get_width()//2,SCREEN_H//2+40))
        if t>0.52:
            la=int(clamp((t-0.52)*6,0,1)*200)
            for i,line in enumerate(["Year 2147. The city never ends"]):
                lt=self.fonts["small"].render(line,True,C["white"]); lt.set_alpha(la)
                surf.blit(lt,(SCREEN_W//2-lt.get_width()//2,SCREEN_H//2+150+i*44))
        sa2=int(abs(math.sin(self.tick*0.08))*180)
        sh=self.fonts["small"].render("[ PRESS ANY KEY TO SKIP ]",True,C["yellow"]); sh.set_alpha(sa2)
        surf.blit(sh,(SCREEN_W//2-sh.get_width()//2,SCREEN_H-60))
        if t>0.88:
            fade=int(clamp((t-0.88)/0.12,0,1)*255)
            fo=pygame.Surface((SCREEN_W,SCREEN_H)); fo.fill((0,0,0)); fo.set_alpha(fade); surf.blit(fo,(0,0))

#HUD
def draw_hud(surf,fonts,player,score,difficulty,biome_name,tick):
    neon_text(surf,fonts["med"],f"{score:,}",C["yellow"],(SCREEN_W//2,30))
    neon_text(surf,fonts["small"],f"\u00d7{difficulty:.1f}  {biome_name}",C["pink"],(SCREEN_W//2,58))
    player.draw_hp(surf,fonts["small"])
    for i in range(2):
        col=C["cyan"] if i<player.jumps_left else (40,40,60)
        pygame.draw.circle(surf,col,(20+i*20,50),6)
        if i<player.jumps_left: draw_glow(surf,col,(20+i*20,50),10,80)
    player.draw_powerup_bar(surf,fonts)

#Screens
class Screen:
    def handle(self,event): pass
    def update(self): pass
    def draw(self,surf): pass

class LoginScreen(Screen):
    def __init__(self,fonts,scores):
        self.fonts=fonts; self.scores=scores; self.tick=0; self.next=None
        self.input=InputBox(SCREEN_W//2,380,400,54,"Enter your name...")
        self.btn=NeonButton(SCREEN_W//2,470,280,56,"ENTER  THE  VOID",C["cyan"])
    def handle(self,event):
        self.input.handle(event)
        if self.btn.clicked(event) and self.input.text.strip(): self.next=("menu",self.input.text.strip())
        if event.type==pygame.KEYDOWN and event.key==pygame.K_RETURN:
            if self.input.text.strip(): self.next=("menu",self.input.text.strip())
    def update(self): self.tick+=1; self.btn.check(pygame.mouse.get_pos())
    def draw(self,surf):
        surf.fill(C["bg"]); _draw_city_bg(surf,self.tick); _draw_scanlines(surf); _draw_grid(surf,self.tick)
        for (x,y,fx,fy) in [(30,30,1,1),(SCREEN_W-30,30,-1,1),(30,SCREEN_H-30,1,-1),(SCREEN_W-30,SCREEN_H-30,-1,-1)]:
            pygame.draw.line(surf,C["cyan"],(x,y),(x+fx*50,y),2)
            pygame.draw.line(surf,C["cyan"],(x,y),(x,y+fy*50),2)
        pulse=0.5+0.5*math.sin(self.tick*0.05); glow_col=lerp_color(C["cyan"],C["pink"],pulse)
        neon_text(surf,self.fonts["big"],"BATTLE FORGE",C["cyan"],(SCREEN_W//2,140))
        pass
        lw=int(300+math.sin(self.tick*0.04)*80)
        ls=pygame.Surface((lw,2),pygame.SRCALPHA); ls.fill((*C["cyan"],160)); surf.blit(ls,(SCREEN_W//2-lw//2,190))
        ls2=pygame.Surface((lw//2,1),pygame.SRCALPHA); ls2.fill((*C["pink"],120)); surf.blit(ls2,(SCREEN_W//2-lw//4,194))
        neon_text(surf,self.fonts["med"],"Cyberpunk Arcade Survivor",C["pink"],(SCREEN_W//2,230))
        self.input.draw(surf,self.fonts["small"]); self.btn.draw(surf,self.fonts["small"])

class MenuScreen(Screen):
    def __init__(self,fonts,username,scores):
        self.fonts=fonts; self.username=username; self.scores=scores; self.tick=0; self.next=None
        cx=SCREEN_W//2
        self.buttons=[
            NeonButton(cx,290,300,58,"▶   PLAY",        C["cyan"]),
            NeonButton(cx,380,300,58,"⊞   LEADERBOARD", C["pink"]),
            NeonButton(cx,470,300,58,"⇌   CHANGE USER",  C["yellow"]),
            NeonButton(cx,560,300,58,"✕   QUIT",         C["red"]),
        ]
    def handle(self,event):
        for btn,act in zip(self.buttons,["play","leaderboard","logout","quit"]):
            if btn.clicked(event): self.next=act
    def update(self): self.tick+=1; mpos=pygame.mouse.get_pos(); [b.check(mpos) for b in self.buttons]
    def draw(self,surf):
        surf.fill(C["bg"]); _draw_city_bg(surf,self.tick); _draw_scanlines(surf); _draw_grid(surf,self.tick)

        # Corner brackets
        for (x,y,fx,fy) in [(30,30,1,1),(SCREEN_W-30,30,-1,1),(30,SCREEN_H-30,1,-1),(SCREEN_W-30,SCREEN_H-30,-1,-1)]:
            pygame.draw.line(surf,C["cyan"],(x,y),(x+fx*50,y),2)
            pygame.draw.line(surf,C["cyan"],(x,y),(x,y+fy*50),2)

        # Animated title pulse
        pulse=0.5+0.5*math.sin(self.tick*0.05)
        neon_text(surf,self.fonts["big"],"BATTLE FORGE",C["cyan"],(SCREEN_W//2,110))

        # Animated separator lines under title
        lw=int(400+math.sin(self.tick*0.04)*60)
        ls=pygame.Surface((lw,2),pygame.SRCALPHA); ls.fill((*C["cyan"],140))
        surf.blit(ls,(SCREEN_W//2-lw//2,158))
        ls2=pygame.Surface((lw//2,1),pygame.SRCALPHA); ls2.fill((*C["pink"],100))
        surf.blit(ls2,(SCREEN_W//2-lw//4,162))

        
        panel_w=380; panel_x=SCREEN_W//2-panel_w//2
        pygame.draw.rect(surf,(10,10,30),(panel_x,168,panel_w,72),border_radius=8)
        draw_neon_rect(surf,C["green"],(panel_x,168,panel_w,72),glow_r=6)
        neon_text(surf,self.fonts["small"],f"OPERATOR:  {self.username}",C["green"],(SCREEN_W//2,185))
        bests=[e["score"] for e in self.scores if e["username"]==self.username]
        best_txt=f"BEST SCORE:  {max(bests):,}" if bests else "BEST SCORE:  ---"
        neon_text(surf,self.fonts["small"],best_txt,C["yellow"],(SCREEN_W//2,215))
        # Decorative side lines beside buttons
        pygame.draw.line(surf,C["purple"],(SCREEN_W//2-200,246),(SCREEN_W//2-200,590),1)
        pygame.draw.line(surf,C["purple"],(SCREEN_W//2+200,246),(SCREEN_W//2+200,590),1)
        pygame.draw.line(surf,C["cyan"],(SCREEN_W//2-200,246),(SCREEN_W//2+200,246),1)
        pygame.draw.line(surf,C["cyan"],(SCREEN_W//2-200,590),(SCREEN_W//2+200,590),1)

        for b in self.buttons: b.draw(surf,self.fonts["small"])

class LeaderboardScreen(Screen):
    def __init__(self,fonts,scores):
        self.fonts=fonts; self.scores=scores; self.tick=0; self.next=None
        self.btn=NeonButton(SCREEN_W//2,SCREEN_H-70,260,52,"← BACK",C["pink"])
    def handle(self,event):
        if self.btn.clicked(event): self.next="menu"
    def update(self): self.tick+=1; self.btn.check(pygame.mouse.get_pos())
    def draw(self,surf):
        surf.fill(C["bg"]); _draw_scanlines(surf)
        neon_text(surf,self.fonts["big"],"LEADERBOARD",C["yellow"],(SCREEN_W//2,70))
        top=sorted(self.scores,key=lambda e:e["score"],reverse=True)[:10]
        rank_cols=[C["yellow"],C["white"],C["orange"]]+[C["cyan"]]*10
        for i,entry in enumerate(top):
            y=148+i*50; col=rank_cols[min(i,len(rank_cols)-1)]
            rs=pygame.Surface((700,42),pygame.SRCALPHA); rs.fill((*tuple(c//6 for c in col[:3]),100))
            surf.blit(rs,(SCREEN_W//2-350,y-4))
            pygame.draw.rect(surf,col,(SCREEN_W//2-350,y-4,700,42),1,border_radius=4)
            surf.blit(self.fonts["med"].render(f"#{i+1}",True,col),(SCREEN_W//2-330,y))
            surf.blit(self.fonts["med"].render(entry["username"],True,col),(SCREEN_W//2-250,y))
            surf.blit(self.fonts["med"].render(f"{entry['score']:,}",True,C["green"]),(SCREEN_W//2+130,y))
            if i<3: draw_glow(surf,col,(SCREEN_W//2-310,y+16),20,50)
        self.btn.draw(surf,self.fonts["small"])

class PauseScreen(Screen):
    def __init__(self,fonts):
        self.fonts=fonts; self.next=None; cx=SCREEN_W//2; cy=SCREEN_H//2
        self.buttons=[NeonButton(cx,cy-20,280,58,"▶   RESUME",C["cyan"]),
                      NeonButton(cx,cy+60,280,58,"↺   RESTART",C["yellow"]),
                      NeonButton(cx,cy+140,280,58,"⌂   MENU",C["pink"])]
    def handle(self,event):
        for btn,act in zip(self.buttons,["resume","restart","menu"]):
            if btn.clicked(event): self.next=act
        if event.type==pygame.KEYDOWN and event.key==pygame.K_ESCAPE: self.next="resume"
    def update(self): mpos=pygame.mouse.get_pos(); [b.check(mpos) for b in self.buttons]
    def draw(self,surf):
        ov=pygame.Surface((SCREEN_W,SCREEN_H),pygame.SRCALPHA); ov.fill((0,0,20,170)); surf.blit(ov,(0,0))
        neon_text(surf,self.fonts["big"],"PAUSED",C["cyan"],(SCREEN_W//2,SCREEN_H//2-160))
        for b in self.buttons: b.draw(surf,self.fonts["small"])

class GameOverScreen(Screen):
    def __init__(self,fonts,score,high_score):
        self.fonts=fonts; self.score=score; self.high_score=high_score; self.tick=0; self.next=None
        cx=SCREEN_W//2; cy=SCREEN_H//2
        self.buttons=[NeonButton(cx,cy+80,280,58,"↺   PLAY AGAIN",C["cyan"]),
                      NeonButton(cx,cy+160,280,58,"⌂   MENU",C["pink"])]
        self.particles=ParticleSystem()
    def handle(self,event):
        for btn,act in zip(self.buttons,["restart","menu"]):
            if btn.clicked(event): self.next=act
    def update(self):
        self.tick+=1; mpos=pygame.mouse.get_pos(); [b.check(mpos) for b in self.buttons]
        if random.random()<0.3:
            self.particles.emit(random.randint(0,SCREEN_W),random.randint(0,SCREEN_H),
                                random.choice([C["red"],C["pink"],C["orange"]]),count=3,speed=2,gravity=0.05,life=60)
        self.particles.update()
    def draw(self,surf):
        ov=pygame.Surface((SCREEN_W,SCREEN_H),pygame.SRCALPHA); ov.fill((20,0,5,200)); surf.blit(ov,(0,0))
        self.particles.draw(surf,0,0)
        col=lerp_color(C["red"],C["pink"],0.5+0.5*math.sin(self.tick*0.05))
        neon_text(surf,self.fonts["big"],"GAME OVER",col,(SCREEN_W//2,SCREEN_H//2-160))
        neon_text(surf,self.fonts["med"],f"Score:  {self.score:,}",C["white"],(SCREEN_W//2,SCREEN_H//2-70))
        neon_text(surf,self.fonts["med"],f"Best:   {self.high_score:,}",C["yellow"],(SCREEN_W//2,SCREEN_H//2-25))
        if self.score>=self.high_score and self.score>0:
            neon_text(surf,self.fonts["small"],"\u2605  NEW HIGH SCORE  \u2605",C["yellow"],(SCREEN_W//2,SCREEN_H//2+20))
        for b in self.buttons: b.draw(surf,self.fonts["small"])

#Game Session
class GameSession:
    def __init__(self,username,scores):
        self.username=username; self.scores=scores
        self.world=World(); self.camera=Camera(); self.particles=ParticleSystem()
        self.player=Player(200,SCREEN_H-300)
        self.bullets=[]; self.enemies=[]; self.bosses=[]; self.powerups=[]; self.dmg_nums=[]
        self.spawner=Spawner(); self.tick=0; self.score=0
        self.distance=0; self.difficulty=1.0; self.combo=0; self.combo_timer=0
        self.paused=False; self.over=False; self.pause_screen=None; self.over_screen=None
        self.powerup_flash=None; self.powerup_flash_timer=0

    def _bi(self): return self.world.biome_at(int(self.camera.x//TILE))

    def handle(self,event,fonts):
        if self.over and self.over_screen: self.over_screen.handle(event); return
        if self.paused and self.pause_screen: self.pause_screen.handle(event); return
        if event.type==pygame.KEYDOWN:
            if event.key in (pygame.K_SPACE,pygame.K_UP,pygame.K_w): self.player.jump()
            if event.key==pygame.K_ESCAPE: self.paused=True; self.pause_screen=PauseScreen(fonts)
            if event.key==pygame.K_f:
                mx,my=pygame.mouse.get_pos(); cx,cy=self.camera.offset()
                self.player.shoot(mx,my,cx,cy,self.bullets,self.particles)
        if event.type==pygame.MOUSEBUTTONDOWN and event.button==1:
            mx,my=pygame.mouse.get_pos(); cx,cy=self.camera.offset()
            self.player.shoot(mx,my,cx,cy,self.bullets,self.particles)

    def update(self,fonts):
        if self.over and self.over_screen: self.over_screen.update(); return self.over_screen.next
        if self.paused and self.pause_screen:
            self.pause_screen.update(); r=self.pause_screen.next
            if r=="resume": self.paused=False
            return r
        if not self.player.alive and not self.over:
            if self.player.death_timer<=0: self._end_game(fonts)
            else: self.player.update(pygame.key.get_pressed(),[])
            return None

        self.tick+=1; self.difficulty=1.0+self.tick/(FPS*45)
        keys=pygame.key.get_pressed()
        platforms=self.world.get_platforms_near(self.camera.x)
        self.player.update(keys,platforms)

        if pygame.mouse.get_pressed()[0] and self.player.alive:
            mx,my=pygame.mouse.get_pos(); cx,cy=self.camera.offset()
            self.player.shoot(mx,my,cx,cy,self.bullets,self.particles)

        self.camera.target(self.player.x,self.player.y); self.camera.update()
        self.distance=int(self.camera.x/10); self.score=self.distance+self.player.score

        if self.combo_timer>0: self.combo_timer-=1
        else: self.combo=0
        if self.powerup_flash_timer>0: self.powerup_flash_timer-=1

        cam_x,cam_y=self.camera.offset()

        # Bullets update
        for b in self.bullets:
            b.update()
            for p in platforms:
                if p.rect.collidepoint(b.x,b.y): b.alive=False; self.particles.emit(b.x,b.y,b.color,5,2); break
        self.bullets=[b for b in self.bullets if b.alive]

        # Spawn
        self.spawner.update(self.enemies,self.bosses,self.powerups,
                            self.player.x,self.player.y,self.world,cam_x,self.difficulty,platforms)

        # Power-up collection
        pr=self.player.rect
        for pu in self.powerups:
            pu.update(platforms)
            if pu.alive and pr.colliderect(pygame.Rect(pu.x,pu.y,pu.W,pu.H)):
                self.player.apply_powerup(pu)
                self.powerup_flash=pu.color; self.powerup_flash_timer=FPS*2
                self.particles.emit(pu.x+pu.W//2,pu.y+pu.H//2,pu.color,20,5,gravity=0.05,life=40)
                pu.alive=False
        self.powerups=[p for p in self.powerups if p.alive]

        # Enemies
        new_enemies=[]
        for e in self.enemies:
            e.update(self.player.x,self.player.y,platforms,self.bullets,self.particles,self.difficulty)
            if not e.alive: continue
            for b in self.bullets:
                if b.owner=="player" and e.rect.collidepoint(b.x,b.y):
                    b.alive=False; killed=e.hit(b.damage,self.particles)
                    self.particles.emit(b.x,b.y,b.color,8,4)
                    if killed:
                        bonus=e.score_val*(1+self.combo//5); self.player.score+=bonus
                        self.dmg_nums.append(DamageNumber(e.x+e.w//2,e.y,bonus,C["yellow"]))
                        self.combo+=1; self.combo_timer=FPS*3
                        # Chance to drop power-up
                        if random.random()<0.12: self.powerups.append(PowerUp(e.x+e.w//2,e.y))
                    else: self.dmg_nums.append(DamageNumber(e.x+e.w//2,e.y,b.damage,C["white"]))
                    if not e.alive: break
            if not e.alive: continue
            if e.rect.colliderect(self.player.rect): self.player.take_damage(1,self.camera,self.particles)
            for b in self.bullets:
                if b.owner=="enemy" and self.player.rect.collidepoint(b.x,b.y):
                    b.alive=False; self.player.take_damage(1,self.camera,self.particles)
            new_enemies.append(e)
        self.enemies=new_enemies

        # Bosses
        new_bosses=[]
        for boss in self.bosses:
            boss.update(self.player.x,self.player.y,platforms,self.bullets,self.particles)
            if not boss.alive: continue
            for b in self.bullets:
                if b.owner=="player" and boss.rect.collidepoint(b.x,b.y):
                    b.alive=False; killed=boss.hit(b.damage,self.particles)
                    self.particles.emit(b.x,b.y,b.color,8,4)
                    if killed:
                        self.player.score+=boss.score_val*(1+self.combo//5)
                        self.dmg_nums.append(DamageNumber(boss.x+boss.W//2,boss.y,boss.score_val,C["gold"]))
                        self.camera.shake_cam(20)
                        # Drop 3 power-ups on boss death
                        for _ in range(3): self.powerups.append(PowerUp(boss.x+random.randint(0,boss.W),boss.y))
                    if not boss.alive: break
            if not boss.alive: continue
            if boss.rect.colliderect(self.player.rect): self.player.take_damage(1,self.camera,self.particles)
            for b in self.bullets:
                if b.owner=="enemy" and self.player.rect.collidepoint(b.x,b.y):
                    b.alive=False; self.player.take_damage(1,self.camera,self.particles)
            new_bosses.append(boss)
        self.bosses=new_bosses
        self.bullets=[b for b in self.bullets if b.alive]
        for d in self.dmg_nums: d.update()
        self.dmg_nums=[d for d in self.dmg_nums if d.alive()]
        self.particles.update()
        return None

    def _end_game(self,fonts):
        self.over=True
        self.scores=add_score(self.scores,self.username,self.score)
        new_best=max([e["score"] for e in self.scores]+[0])
        self.over_screen=GameOverScreen(fonts,self.score,new_best)

    def draw(self,surf,fonts):
        cam_x,cam_y=self.camera.offset(); bi=self._bi()
        self.world.draw_bg(surf,cam_x,cam_y,bi)
        self.world.draw_stars(surf,self.world.get_stars_near(cam_x),cam_x,cam_y)
        _draw_scanlines(surf)
        platforms=self.world.get_platforms_near(cam_x)
        self.world.draw_platforms(surf,platforms,cam_x,cam_y,self.tick)
        self.particles.draw(surf,cam_x,cam_y)
        for pu in self.powerups: pu.draw(surf,cam_x,cam_y)
        for e in self.enemies: e.draw(surf,cam_x,cam_y,self.tick)
        for boss in self.bosses: boss.draw(surf,cam_x,cam_y,self.tick)
        for b in self.bullets: b.draw(surf,cam_x,cam_y)
        self.player.draw(surf,cam_x,cam_y,self.tick)
        for d in self.dmg_nums: d.draw(surf,fonts["small"],cam_x,cam_y)
        draw_hud(surf,fonts,self.player,self.score,self.difficulty,BIOMES[bi]["name"],self.tick)
        for boss in self.bosses: boss.draw_hud_bar(surf,fonts)
        # Power-up pickup flash
        if self.powerup_flash and self.powerup_flash_timer>0:
            t=self.powerup_flash_timer/(FPS*2)
            fl=pygame.Surface((SCREEN_W,SCREEN_H),pygame.SRCALPHA)
            fl.fill((*self.powerup_flash,int(40*t))); surf.blit(fl,(0,0))
            pd=next((p for p in POWERUP_TYPES if p["color"]==self.powerup_flash),None)
            if pd:
                label_alpha=int(255*t)
                lt=fonts["med"].render(pd["label"]+" !",True,self.powerup_flash); lt.set_alpha(label_alpha)
                surf.blit(lt,(SCREEN_W//2-lt.get_width()//2,SCREEN_H//2-40))
        # Combo
        if self.combo>=2:
            col=lerp_color(C["yellow"],C["orange"],0.5+0.5*math.sin(self.tick*0.15))
            neon_text(surf,fonts["med"],f"COMBO \u00d7{self.combo}",col,(SCREEN_W-160,50))
        # Boss warning
        if self.bosses:
            wa=int(abs(math.sin(self.tick*0.1))*200)+55
            wt=fonts["small"].render("⚠  BOSS INCOMING  ⚠",True,C["red"]); wt.set_alpha(wa)
            # Already shown via boss HP bar, skip extra text if bar is visible
        if self.paused and self.pause_screen: self.pause_screen.draw(surf)
        if self.over and self.over_screen: self.over_screen.draw(surf)

#Main
def main():
    pygame.init(); pygame.display.set_caption("BATTLE FORGE")
    screen=pygame.display.set_mode((SCREEN_W,SCREEN_H)); clock=pygame.time.Clock()

    def make_fonts():
        for name in ["Courier New","Consolas","Courier","monospace",None]:
            try:
                return {"big":pygame.font.SysFont(name,72,bold=True),
                        "med":pygame.font.SysFont(name,36,bold=True),
                        "small":pygame.font.SysFont(name,24)}
            except: pass
        return {"big":pygame.font.Font(None,80),"med":pygame.font.Font(None,44),"small":pygame.font.Font(None,28)}

    fonts=make_fonts(); scores=load_scores()
    state="intro"; username=""; screen_obj=IntroSequence(fonts); session=None

    running=True
    while running:
        events=pygame.event.get()
        for event in events:
            if event.type==pygame.QUIT: running=False
            if state=="game" and session: session.handle(event,fonts)
            else: screen_obj.handle(event)

        if state=="intro":
            screen_obj.update()
            if screen_obj.done: state="login"; screen_obj=LoginScreen(fonts,scores)
        elif state=="login":
            screen_obj.update()
            if screen_obj.next: _,username=screen_obj.next; state="menu"; screen_obj=MenuScreen(fonts,username,scores)
        elif state=="menu":
            screen_obj.update(); nxt=screen_obj.next
            if nxt=="play": session=GameSession(username,scores); state="game"; screen_obj=session
            elif nxt=="leaderboard": state="leaderboard"; screen_obj=LeaderboardScreen(fonts,scores)
            elif nxt=="logout": state="login"; screen_obj=LoginScreen(fonts,scores)
            elif nxt=="quit": running=False
        elif state=="leaderboard":
            screen_obj.update()
            if screen_obj.next=="menu": state="menu"; screen_obj=MenuScreen(fonts,username,scores)
        elif state=="game":
            result=session.update(fonts); scores=session.scores
            if result=="restart": session=GameSession(username,scores); screen_obj=session
            elif result=="menu": state="menu"; session=None; screen_obj=MenuScreen(fonts,username,scores)

        screen.fill(C["bg"])
        if state=="game" and session: session.draw(screen,fonts)
        else: screen_obj.draw(screen)
        pygame.display.flip(); clock.tick(FPS)

    pygame.quit(); sys.exit()

if __name__=="__main__":
    main()
