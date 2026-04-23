# Obstacle Avoidance — PR2 Controller

## System Schema

```
┌─────────────────────────────────────────────────────────────────┐
│                        Webots World                             │
│                                                                 │
│   ┌──────────────────────────────────────────────────────┐     │
│   │                     PR2 Robot                        │     │
│   │                                                      │     │
│   │  ┌─────────────┐        ┌─────────────┐             │     │
│   │  │   ds_left   │        │  ds_right   │             │     │
│   │  │ pos: front  │        │ pos: front  │             │     │
│   │  │ angle:+0.15 │        │ angle:-0.15 │             │     │
│   │  │ range: 2.0m │        │ range: 2.0m │             │     │
│   │  │  7 rays     │        │  7 rays     │             │     │
│   │  └──────┬──────┘        └──────┬──────┘             │     │
│   │         │                      │                    │     │
│   │         └──────────┬───────────┘                    │     │
│   │                    │                                │     │
│   │         ┌──────────▼──────────┐                     │     │
│   │         │  obstacle_avoidance │                     │     │
│   │         │  .py                │                     │     │
│   │         │  navigate_with_     │                     │     │
│   │         │  avoidance()        │                     │     │
│   │         └──────────┬──────────┘                     │     │
│   │                    │                                │     │
│   │         ┌──────────▼──────────┐                     │     │
│   │         │   pr2_control.py    │                     │     │
│   │         │  robot_go_forward() │                     │     │
│   │         │  robot_go_sideways()│                     │     │
│   │         │  robot_rotate()     │                     │     │
│   │         └──────────┬──────────┘                     │     │
│   │                    │                                │     │
│   │         ┌──────────▼──────────┐                     │     │
│   │         │   8 caster wheels   │                     │     │
│   │         └─────────────────────┘                     │     │
│   └──────────────────────────────────────────────────────┘     │
│                                                                 │
│   obstacle1 (−5.64, 0.25)     table1 (−0.26, 0)               │
│   PR2 start  (−4.64, 0.26)    table2 (−7.97, 0)  ← goal       │
└─────────────────────────────────────────────────────────────────┘
```

---

## Step-by-Step Guideline

### Step 1 — World Setup (`my_project_world.wbt`)

Two `DistanceSensor` nodes are attached to the PR2 via `baseSlot`:

| Property | ds_left | ds_right |
|---|---|---|
| Position | front-left of base | front-right of base |
| Angle | +0.15 rad (angled left) | −0.15 rad (angled right) |
| Range | 2.0 m | 2.0 m |
| Rays | 7 | 7 |
| Aperture | 0.9 rad (~52°) | 0.9 rad (~52°) |
| lookupTable | 0 m → 1.0, 2.0 m → 0.0 | same |

`getValue()` formula:
```
value    = 1 - (distance / 2.0)
distance = (1 - value) × 2.0
```

---

### Step 2 — Enable from Config (`configs/experiment1.json`)

```json
"obstacle_avoidance": true
```

Read in `pr2_controller.py` → passed as `avoid_obstacles=True` to the `navigate_and_pickup` task.

---

### Step 3 — Entry Point (`task.py → move()`)

When `avoid_obstacles=True`:
1. Compute initial heading error to goal
2. Rotate to face goal (`robot_rotate`)
3. Initialize both sensors (`oa.init_sensors`)
4. Hand over to `oa.navigate_with_avoidance()` — runs until `"DONE"` or `"HALTED"`

---

### Step 4 — Main Loop (`obstacle_avoidance.py → navigate_with_avoidance`)

Every iteration:

```
① Compute dist_to_goal
   └─ < 0.30 m  →  STOP, return "DONE"

② Check goal_node contact
   └─ touching  →  STOP, return "DONE"

③ Resilience check
   └─ not resilient + no mitigation  →  STOP, return "HALTED"

④ Read ds_left, ds_right  (values 0.0 – 1.0)
   └─ dist_to_goal < 1.2 m  →  force both = 0.0  (near-goal zone)

⑤ Decide action:

   left > 0.75 AND right > 0.75          → EMERGENCY
   ├─ back up 0.3 m
   └─ strafe 0.5 m toward clearer side

   left > 0.50 OR right > 0.50           → AVOIDANCE
   ├─ obstacle on LEFT  → strafe RIGHT  −0.5 m
   └─ obstacle on RIGHT → strafe LEFT   +0.5 m

   else (clear path)                      → FREE DRIVE
   ├─ heading error > 0.10 rad → rotate to face goal
   └─ drive forward min(0.35 m, dist_to_goal)
```

---

### Step 5 — Flowchart

```
                        START
                          │
                          ▼
               ┌─ dist_to_goal < 0.30 m? ──────────────────► STOP → return "DONE"
               │  or goal_node contact?
               │  No
               ▼
        ┌─ resilience OK? ─────────────────────────────────► STOP → return "HALTED"
        │  Yes
        ▼
   Read ds_left, ds_right
        │
        ├─ dist_to_goal < 1.2 m? ──► force left=0, right=0  (near-goal zone)
        │
        ▼
┌──────────────────────────────────────────────────────────────────────┐
│  IF  left > 0.75  AND  right > 0.75   (both sensors, ~0.5 m)        │
│       → EMERGENCY                                                    │
│         1. Back up  0.3 m                                            │
│         2. Strafe toward clearer side  0.5 m                         │
├──────────────────────────────────────────────────────────────────────┤
│  ELIF  left > 0.50  OR  right > 0.50   (one sensor, ~1.0 m)         │
│       → AVOIDANCE                                                    │
│         obstacle on LEFT  → strafe RIGHT  −0.5 m                    │
│         obstacle on RIGHT → strafe LEFT   +0.5 m                    │
├──────────────────────────────────────────────────────────────────────┤
│  ELSE  (path clear)                                                  │
│       → FREE DRIVE                                                   │
│         1. If heading error > 0.10 rad → rotate to face goal         │
│         2. Drive forward  min(0.35 m, dist_to_goal)                  │
└──────────────────────────────────────────────────────────────────────┘
        │
        └──────────────────────────────► loop back to START
```

---

### Step 6 — Wheel Primitives (`pr2_control.py`)

| Function | Caster angle | Effect |
|---|---|---|
| `robot_go_forward(d)` | 0 rad | move forward (`d>0`) or backward (`d<0`) |
| `robot_go_sideways(d)` | ±π/2 rad | strafe left (`d>0`) / right (`d<0`) |
| `robot_rotate(angle)` | ±3π/4, ±π/4 | rotate in place |

All three functions set caster rotation joints first, then use wheel encoder feedback to travel the exact distance before resetting casters to 0.

---

## Sensor Value → Distance Reference

| `getValue()` | Distance to obstacle | Action triggered |
|---|---|---|
| 0.00 | 2.0 m | nothing |
| 0.50 | 1.0 m | **avoidance strafe** starts |
| 0.75 | 0.5 m | **emergency** backup + strafe |
| 1.00 | 0.0 m | contact |

---

## Tunable Parameters

| Parameter | File | Current value | Effect |
|---|---|---|---|
| `AVOIDANCE_THRESHOLD` | `obstacle_avoidance.py` | 0.50 → 1.0 m | lower = react sooner |
| `STOP_THRESHOLD` | `obstacle_avoidance.py` | 0.75 → 0.5 m | must always be > AVOIDANCE_THRESHOLD |
| `STRAFE_DISTANCE` | `obstacle_avoidance.py` | 0.5 m | wider strafe clears bigger objects |
| `NEAR_GOAL_ZONE` | `obstacle_avoidance.py` | 1.2 m | prevents goal table being treated as obstacle |
| `STEP_DISTANCE` | `obstacle_avoidance.py` | 0.35 m | forward step size per iteration |
| `HEADING_TOLERANCE` | `obstacle_avoidance.py` | 0.10 rad | minimum error before re-orienting |
| `numberOfRays` | `my_project_world.wbt` | 7 | more rays = wider detection reliability |
| `aperture` | `my_project_world.wbt` | 0.9 rad | cone width of each sensor (~52°) |
| lookupTable range | `my_project_world.wbt` | 2.0 m | max detection distance |

---

## File Overview

```
pr2_controller/
├── obstacle_avoidance.py     ← main avoidance logic (navigate_with_avoidance)
├── pr2_control.py            ← wheel primitives (go_forward, go_sideways, rotate)
├── task.py                   ← entry point (move() calls navigate_with_avoidance)
├── pr2_controller.py         ← reads "obstacle_avoidance" flag from config
├── components/
│   └── distance_sensor.py    ← DistanceSensor device wrapper
└── configs/
    └── experiment1.json      ← set "obstacle_avoidance": true / false
```
