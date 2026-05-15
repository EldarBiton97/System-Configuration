# X-Ray Interaction-Free Measurement Configuration Visualizer

An interactive web-based ray-tracing tool for planning and visualizing X-ray Interaction-Free Measurement (IFM) experiments at the ESRF. 

This tool simulates the geometry of the beam propagation through a monolithic Silicon(333) crystal LLL interferometer, allowing researchers to calculate Bragg angles, predict beam splitting, and position experimental components (wedges and detectors) in real-time.

### Live Demo
**[Launch the Visualizer](http://Eldar3103.pythonanywhere.com)**

### Key Features
* **Real-Time Ray Tracing:** Adjust the incident beam offset and energy (keV) to calculate the Si(333) Bragg angle and instantly visualize the beam paths.
* **Component Positioning:** Interactive sliders to place the phase wedge, the "bomb" (blocking detector), and the final AdvaPIX camera.
* **Dynamic Beam Masking:** Uses the Liang-Barsky clipping algorithm to accurately simulate beam blocking when the "bomb" is moved into the optical path.
* **History Tracking:** Automatically calculates and labels the transmission (T) and reflection (R) history of every beam path, maintaining consistent color-coding regardless of beam obstruction.

### Local Setup & Development
To run this visualizer on your own machine:

1. **Clone the repository:**
   `git clone https://github.com/EldarBiton97/System-Configuration.git`
   `cd System-Configuration`

2. **Install the dependencies:**
   This project requires Python 3.10+. Install the required libraries using the `requirements.txt` file:
   `pip install -r requirements.txt`

3. **Run the app:**
   `python system_config_esrf.py`

4. Open a web browser and go to `http://127.0.0.1:8050/`.