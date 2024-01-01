#version 120

uniform mat4 mat_m;
uniform mat4 mat_v;
uniform mat4 mat_p;

attribute vec3 position;

varying float height;
varying float vertex_id;

void main()
{
  gl_Position = mat_p * mat_v * mat_m * vec4(position, 1.0);
  height = position.z;
  //vertex_id = gl_VertexID;
}