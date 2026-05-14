import dash
from dash import dcc, html, Input, Output
import numpy as np
import plotly.graph_objects as go

# Initialize the Dash app
app = dash.Dash(__name__)
server = app.server
app.title = "X-Ray IFM Simulator"

# --- Layout (The User Interface) ---
app.layout = html.Div(style={'fontFamily': 'Arial, sans-serif', 'padding': '20px'}, children=[
    html.H1("X-Ray Interaction-Free Measurement Simulator", style={'textAlign': 'center'}),

    html.Div(style={'display': 'flex', 'justifyContent': 'space-around', 'paddingBottom': '20px'}, children=[
        # Column 1
        html.Div(style={'width': '30%'}, children=[
            html.Label("Energy (keV)"),
            dcc.Slider(id='energy', min=7.0, max=30.0, step=0.5, value=30.0, updatemode='drag',
                       tooltip={"placement": "bottom", "always_visible": True}),
            html.Br(),
            html.Label("Beam Offset Y"),
            dcc.Slider(id='beam_y', min=-15.0, max=15.0, step=0.5, value=0.0, updatemode='drag',
                       tooltip={"placement": "bottom", "always_visible": True}),
            html.Br(),
            html.Label("Wedge X"),
            dcc.Slider(id='wedge_x', min=0.0, max=22.0, step=0.5, value=15.0, updatemode='drag',
                       tooltip={"placement": "bottom", "always_visible": True}),
        ]),

        # Column 2
        html.Div(style={'width': '30%'}, children=[
            html.Label("Wedge Y"),
            dcc.Slider(id='wedge_y', min=-30.0, max=30.0, step=0.5, value=20.0, updatemode='drag',
                       tooltip={"placement": "bottom", "always_visible": True}),
            html.Br(),
            html.Label("Bomb X"),
            dcc.Slider(id='bomb_x', min=0.0, max=60.0, step=0.5, value=28.0, updatemode='drag',
                       tooltip={"placement": "bottom", "always_visible": True}),
            html.Br(),
            html.Label("Bomb Y"),
            dcc.Slider(id='bomb_y', min=-100.0, max=50.0, step=0.5, value=-50.0, updatemode='drag',
                       tooltip={"placement": "bottom", "always_visible": True}),
        ]),

        # Column 3
        html.Div(style={'width': '30%'}, children=[
            html.Label("Camera Distance"),
            dcc.Slider(id='cam_dist', min=10.0, max=150.0, step=1.0, value=60.0, updatemode='drag',
                       tooltip={"placement": "bottom", "always_visible": True}),
        ]),
    ]),

    html.Hr(),

    # The Plot
    dcc.Graph(id='sim-plot', style={'height': '70vh'})
])


# --- Callbacks (The Real-Time Engine) ---
@app.callback(
    Output('sim-plot', 'figure'),
    [Input('energy', 'value'),
     Input('beam_y', 'value'),
     Input('wedge_x', 'value'),
     Input('wedge_y', 'value'),
     Input('bomb_x', 'value'),
     Input('bomb_y', 'value'),
     Input('cam_dist', 'value')]
)
def update_plot(energy_kev, beam_y_offset, wedge_x, wedge_y, int_detector_x, int_detector_y, out_len):
    fig = go.Figure()

    # Physics parameters (Si(111) diffraction planes)
    wavelength_A = 12.398 / energy_kev
    a_Si = 5.431
    d_333 = a_Si / np.sqrt(27)

    sin_theta = wavelength_A / (2 * d_333)
    if sin_theta > 1.0:
        return fig.update_layout(title="Energy too low for Bragg diffraction on Si(111)")

    theta_B_rad = np.arcsin(sin_theta)
    theta_B_deg = np.degrees(theta_B_rad)
    m = np.tan(theta_B_rad)

    # Geometry parameters
    L = 22.0
    t = 0.15  # 150 microns

    # Blade height 20mm (from -10 to +10)
    y_blade_min, y_blade_max = -10.0, 10.0
    x_blade1, x_blade2, x_blade3 = 0, L + t, 2 * L + 2 * t
    det_x = x_blade3 + t + out_len

    # Bomb parameters
    body_width, body_depth = 60.0, 10.0
    bx_min, bx_max = int_detector_x - body_depth / 2, int_detector_x + body_depth / 2
    by_min, by_max = int_detector_y - body_width / 2, int_detector_y + body_width / 2

    shapes, annotations = [], []

    def add_rect(x0, y0, x1, y1, fillcolor, line_color, opacity=1.0):
        shapes.append(
            dict(type="rect", x0=x0, y0=y0, x1=x1, y1=y1, fillcolor=fillcolor, line=dict(color=line_color, width=1.2),
                 opacity=opacity, layer="below"))

    # 1. Draw Blades (Exactly 150 microns thick, 20mm tall)
    for x_start, label in [(x_blade1, 'Blade 1'), (x_blade2, 'Blade 2'), (x_blade3, 'Blade 3')]:
        add_rect(x_start, y_blade_min, x_start + t, y_blade_max, '#a0c4ff', 'black', 0.8)

    # 2. Draw Camera Body (Massive black box)
    add_rect(det_x, -100, det_x + 50, 100, 'black', 'black')

    # 3. Draw AdvaPIX Sensor Chip (28mm grey chip on the front of the camera)
    chip_length = 0.055*512
    add_rect(det_x - 1, -chip_length / 2, det_x, chip_length / 2, 'gray', 'white')
    annotations.append(dict(x=det_x + 25, y=0, text='AdvaPIX Camera', showarrow=False, font=dict(color='red')))

    # 4. Draw Bomb
    add_rect(bx_min, by_min, bx_max, by_max, '#555555', 'black')

    # 5. Draw Wedge
    wedge_length = 20.0
    half_base = wedge_length * np.tan(np.radians(2.8 / 2))
    shapes.append(dict(type="path",
                       path=f"M {wedge_x - half_base} {wedge_y} L {wedge_x + half_base} {wedge_y} L {wedge_x} {wedge_y - wedge_length} Z",
                       fillcolor='#add8e6', line=dict(color='#00008b', width=1.5), opacity=0.7, layer="above"))

    # Ray Tracing (1mm thick polygons)
    def draw_beam_segment(start_x, start_y, end_x, end_y, color, label=None):
        thickness = 1.0
        vec = np.array([end_x - start_x, end_y - start_y])
        length = np.linalg.norm(vec)
        if length == 0: return
        dir_vec = vec / length
        perp_vec = np.array([-dir_vec[1], dir_vec[0]])

        half_t = thickness / 2.0
        p1 = np.array([start_x, start_y]) + perp_vec * half_t
        p2 = np.array([start_x, start_y]) - perp_vec * half_t
        p3 = np.array([end_x, end_y]) - perp_vec * half_t
        p4 = np.array([end_x, end_y]) + perp_vec * half_t

        fig.add_trace(go.Scatter(
            x=[p1[0], p2[0], p3[0], p4[0], p1[0]],
            y=[p1[1], p2[1], p3[1], p4[1], p1[1]],
            fill='toself', fillcolor=color, mode='lines',
            line=dict(color=color, width=0), opacity=0.85,
            name=label if label else '',
            showlegend=bool(label),
            hoverinfo='name' if label else 'skip'
        ))

    def propagate(x_start, y_start, slope, color, target_x, label=None):
        y_target = y_start + slope * (target_x - x_start)

        # Bomb Clipping
        dx, dy = target_x - x_start, y_target - y_start
        p = [-dx, dx, -dy, dy]
        q = [x_start - bx_min, bx_max - x_start, y_start - by_min, by_max - y_start]
        u1, u2 = 0.0, 1.0
        for i in range(4):
            if p[i] == 0:
                if q[i] < 0: u2 = -1
            else:
                t_val = q[i] / p[i]
                if p[i] < 0 and t_val > u1:
                    u1 = t_val
                elif p[i] > 0 and t_val < u2:
                    u2 = t_val

        if u1 <= u2 and u1 <= 1.0 and u2 >= 0.0:
            draw_beam_segment(x_start, y_start, x_start + u1 * dx, y_start + u1 * dy, color, label)
            return None
        else:
            draw_beam_segment(x_start, y_start, target_x, y_target, color, label)
            return y_target

    def process_blade(beams_in, blade_x, blade_idx):
        beams_out = []
        for bx, by, bslope, hist in beams_in:
            y_target = propagate(bx, by, bslope, '#A0A0A0', blade_x + t / 2)
            if y_target is not None:
                if y_blade_min <= y_target <= y_blade_max:
                    beams_out.append(
                        (blade_x + t / 2, y_target, bslope, f"{hist}*T{blade_idx}" if hist else f"T{blade_idx}"))
                    beams_out.append(
                        (blade_x + t / 2, y_target, -bslope, f"{hist}*R{blade_idx}" if hist else f"R{blade_idx}"))
                else:
                    beams_out.append((blade_x + t / 2, y_target, bslope, hist))
        return beams_out

    # Execution
    inc_start_y = beam_y_offset - (10 + t / 2) * m
    beams_leaving_1 = process_blade([(-10, inc_start_y, m, "")], x_blade1, 1)
    beams_leaving_2 = process_blade(beams_leaving_1, x_blade2, 2)
    beams_leaving_3 = process_blade(beams_leaving_2, x_blade3, 3)

    unique_ports = {}
    for bx, by, bslope, hist in beams_leaving_3:
        state_key = (round(bx, 4), round(by, 4), round(bslope, 4))
        if state_key not in unique_ports: unique_ports[state_key] = []
        if hist: unique_ports[state_key].append(hist)

    # Compile the final data before plotting
    final_beams = []
    for state_key, hists in unique_ports.items():
        bx, by, bslope = state_key
        combined_hist = " + ".join(sorted(hists)) if hists else "Direct Miss"
        # Math calculation: Predict exactly where this beam will strike the camera
        y_at_camera = by + bslope * (det_x - bx)
        final_beams.append({
            'bx': bx, 'by': by, 'bslope': bslope,
            'hist': combined_hist, 'y_cam': y_at_camera
        })

    # STEP 1: Lock the colors alphabetically so crossing beams never magically swap colors
    sorted_hists = sorted(list(set([b['hist'] for b in final_beams])))
    colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b', '#e377c2', '#7f7f7f']
    color_map = {hist: colors[i % len(colors)] for i, hist in enumerate(sorted_hists)}

    # STEP 2: Sort the plotting order strictly by their Y position at the camera (highest to lowest)
    final_beams.sort(key=lambda b: b['y_cam'], reverse=True)

    # Plot the beams in this dynamic top-to-bottom order!
    for beam in final_beams:
        propagate(beam['bx'], beam['by'], beam['bslope'], color_map[beam['hist']], det_x, label=beam['hist'])

    fig.update_layout(
        title=f"Si(111) Ray Tracing | Energy = {energy_kev:.2f} keV | θ_B ≈ {theta_B_deg:.2f}°",
        xaxis=dict(title='Propagation Distance (mm)', range=[-15, 170]),
        yaxis=dict(title='Transverse Distance (mm)', range=[-35, 35], scaleanchor="x", scaleratio=1),
        shapes=shapes, annotations=annotations,
        margin=dict(l=40, r=40, t=60, b=120),
        legend=dict(
            orientation="h",
            yanchor="top",
            y=-0.15,
            xanchor="center",
            x=0.5
        ),
        plot_bgcolor="white",
        uirevision='constant',
        showlegend=True
    )

    fig.update_xaxes(showgrid=False, zeroline=False)
    fig.update_yaxes(showgrid=False, zeroline=False)

    return fig


if __name__ == '__main__':
    app.run(debug=True)