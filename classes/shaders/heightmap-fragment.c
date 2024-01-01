#version 120

varying float height;
varying float vertex_id;

uniform float height_min;
uniform float height_max;

void main()
{
  
  float r, g, b;

  // calculate a 7-step color spectrum
  float a = 6 * (height - height_min) / (height_max - height_min); // normalize
  float x = floor(a);
  float y = a-x;
  
  if (x == 0)      { r=0.2; g=0.2;  b=y;   } // grey
  else if (x == 1) { r=0;   g=y;    b=1;   } // blue
  else if (x == 2) { r=0;   g=1;    b=1-y; } // light blue
  else if (x == 3) { r=y;   g=1-y;  b=0;   } // green
  else if (x == 4) { r=1;   g=y;    b=0;   } // red
  else if (x == 5) { r=1;   g=1;    b=y;   } // yellow
  else if (x == 6) { r=1;   g=1;    b=1;   } // white
  else             { r=1;   g=1;    b=1;   } // white
  
  if (height_max == 0 && height_min == 0) {
    gl_FragColor = vec4(1, 1, 1, 0.1);
  } else {
    gl_FragColor = vec4(r, g, b, 0.5);
  }
  
  // simple way of striping the surface
  //if (mod(floor(vertex_id), 10) == 0) {
  //  gl_FragColor = vec4(r, g, b, 0.7);
  //}
}