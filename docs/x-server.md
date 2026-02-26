This page is for more info on how I do the X11 server.

This is the explanation to the `xorg.conf` file:

- `Module` tells Xorg to load the GLX extension — this is what enables OpenGL inside X11. Without it Genesis's viewer won't render
- `Device` defines a virtual graphics card using the dummy driver (the xserver-xorg-video-dummy package you installed). It's a fake GPU that exists purely in software. VideoRam 256000 gives it ~256MB of virtual VRAM
- `Monitor` defines a fake monitor. HorizSync and VertRefresh are the supported frequency ranges — these are standard values that just need to be plausible, they don't correspond to real hardware.
- `Screen` ties the device and monitor together and sets the resolution. DefaultDepth 24 means 24-bit color (standard RGB). The Modes line inside Display is where the actual resolution is set
- `ServerLayout` is the top-level config that assembles everything into one virtual display
