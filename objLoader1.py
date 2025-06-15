import math
import os
import numpy as np
from dataclasses import dataclass, field
from typing import List, Optional

# --- Data Classes for OBJ Loader ---
@dataclass
class Vector2:
    x: float = 0.0
    y: float = 0.0

    def __eq__(self, other: 'Vector2') -> bool:
        return self.x == other.x and self.y == other.y

    def __add__(self, other: 'Vector2') -> 'Vector2':
        return Vector2(self.x + other.x, self.y + other.y)

    def __sub__(self, other: 'Vector2') -> 'Vector2':
        return Vector2(self.x - other.x, self.y - other.y)

    def __mul__(self, scalar: float) -> 'Vector2':
        return Vector2(self.x * scalar, self.y * scalar)

@dataclass
class Vector3:
    x: float = 0.0
    y: float = 0.0
    z: float = 0.0

    def __eq__(self, other: 'Vector3') -> bool:
        return self.x == other.x and self.y == other.y and self.z == other.z

    def __add__(self, other: 'Vector3') -> 'Vector3':
        return Vector3(self.x + other.x, self.y + other.y, self.z + other.z)

    def __sub__(self, other: 'Vector3') -> 'Vector3':
        return Vector3(self.x - other.x, self.y - other.y, self.z - other.z)

    def __mul__(self, scalar: float) -> 'Vector3':
        return Vector3(self.x * scalar, self.y * scalar, self.z * scalar)

    def __truediv__(self, scalar: float) -> 'Vector3':
        return Vector3(self.x / scalar, self.y / scalar, self.z / scalar)

    def dot(self, other: 'Vector3') -> float:
        return self.x * other.x + self.y * other.y + self.z * other.z

    def cross(self, other: 'Vector3') -> 'Vector3':
        return Vector3(
            self.y * other.z - self.z * other.y,
            self.z * other.x - self.x * other.z,
            self.x * other.y - self.y * other.x
        )

    def magnitude(self) -> float:
        return math.sqrt(self.x**2 + self.y**2 + self.z**2)

@dataclass
class Vertex:
    position: Vector3
    normal: Vector3 = field(default_factory=Vector3)
    texcoord: Vector2 = field(default_factory=Vector2)

@dataclass
class Material:
    name: str = ''
    Ka: Vector3 = field(default_factory=Vector3)
    Kd: Vector3 = field(default_factory=Vector3)
    Ks: Vector3 = field(default_factory=Vector3)
    Ns: float = 0.0
    Ni: float = 0.0
    d: float = 1.0
    illum: int = 0
    map_Ka: str = ''
    map_Kd: str = ''
    map_Ks: str = ''
    map_Ns: str = ''
    map_d: str = ''
    map_bump: str = ''

@dataclass
class Mesh:
    name: str
    vertices: List[Vertex]
    indices: List[int]
    materials: Optional[Material] = None

# --- Utility Functions ---
def first_token(line: str) -> str:
    return line.strip().split(None, 1)[0] if line.strip() else ''

def tail(line: str) -> str:
    parts = line.strip().split(None, 1)
    return parts[1] if len(parts) > 1 else ''

def split_token(s: str, token: str) -> List[str]:
    return s.split(token)

def get_elem(lst: List, idx_str: str):
    idx = int(idx_str)
    if idx < 0:
        return lst[len(lst) + idx]
    return lst[idx - 1]

# --- OBJ Loader with Console Logging ---
class Loader:
    def __init__(self):
        self.meshes: List[Mesh] = []
        self.materials: List[Material] = []
        self.vertices_all: List[Vertex] = []
        self.indices_all: List[int] = []

    def load(self, path: str) -> bool:
        if not path.lower().endswith('.obj'):
            print(f"Error: Not an .obj file: {path}")
            return False
        try:
            file = open(path, 'r')
        except IOError:
            print(f"Error: Cannot open file: {path}")
            return False

        print(f"Loading OBJ: {path}")
        positions: List[Vector3] = []
        tcoords: List[Vector2] = []
        normals: List[Vector3] = []
        verts: List[Vertex] = []
        inds: List[int] = []
        mat_names: List[str] = []
        current_name = ''
        listening = False
        output_every = 1000
        counter = 0

        def log_progress():
            print(f"- {current_name}	| vertices > {len(positions)}	| texcoords > {len(tcoords)}"
                  f"	| normals > {len(normals)}	| triangles > {len(verts)//3}"
                  + (f"	| material: {mat_names[-1]}" if mat_names else ""))

        for line in file:
            counter += 1
            if counter % output_every == 1 and listening:
                log_progress()

            token = first_token(line)
            if token in ('o', 'g'):
                if not listening:
                    listening = True
                else:
                    if verts and inds:
                        # finalize with last material name if available
                        mat = mat_names[-1] if mat_names else None
                        self._finalize_mesh(current_name, verts, inds, mat)
                    verts, inds = [], []
                current_name = tail(line) or 'unnamed'
                print(f"Object/Group: {current_name}")
                continue

            if token == 'v':
                x,y,z = map(float, tail(line).split())
                positions.append(Vector3(x,y,z))
            elif token == 'vt':
                u,v = map(float, tail(line).split())
                tcoords.append(Vector2(u,v))
            elif token == 'vn':
                x,y,z = map(float, tail(line).split())
                normals.append(Vector3(x,y,z))
            elif token == 'f':
                face_verts = []
                for part in tail(line).split():
                    comps = part.split('/')
                    v = Vertex(position=get_elem(positions, comps[0]))
                    if len(comps) > 1 and comps[1]:
                        v.texcoord = get_elem(tcoords, comps[1])
                    if len(comps) > 2 and comps[2]:
                        v.normal = get_elem(normals, comps[2])
                    face_verts.append(v)
                # auto-normal
                if any(v.normal == Vector3() for v in face_verts):
                    A = face_verts[0].position - face_verts[1].position
                    B = face_verts[2].position - face_verts[1].position
                    n = A.cross(B)
                    for v in face_verts:
                        v.normal = n
                for i in range(1, len(face_verts)-1):
                    tri = [face_verts[0], face_verts[i], face_verts[i+1]]
                    base = len(verts)
                    verts.extend(tri)
                    inds.extend([base, base+1, base+2])
                    self.vertices_all.extend(tri)
                    self.indices_all.extend([base, base+1, base+2])
            elif token == 'usemtl':
                mat = tail(line)
                mat_names.append(mat)
                print(f"Use material: {mat}")
                if verts and inds:
                    self._finalize_mesh(current_name, verts, inds, mat)
                    verts, inds = [], []
            elif token == 'mtllib':
                mtl = tail(line)
                mtl_path = os.path.join(os.path.dirname(path), mtl)
                print(f"Loading materials from: {mtl_path}")
                self._load_mtl(mtl_path)

        if verts and inds:
            mat = mat_names[-1] if mat_names else None
            self._finalize_mesh(current_name, verts, inds, mat)
        file.close()
        print("Finished loading OBJ")
        return True

    def _finalize_mesh(self, name: str, verts: List[Vertex], inds: List[int], mat_name: Optional[str]):
        mesh_mat = None
        if mat_name:
            mesh_mat = next((m for m in self.materials if m.name == mat_name), None)
        mesh = Mesh(name=name, vertices=list(verts), indices=list(inds), materials=mesh_mat)
        self.meshes.append(mesh)

    def _load_mtl(self, path: str) -> bool:
        if not path.lower().endswith('.mtl'):
            return False
        try:
            file = open(path, 'r')
        except IOError:
            print(f"Error: Cannot open MTL file: {path}")
            return False
        print(f"Parsing MTL: {path}")
        current: Optional[Material] = None
        for line in file:
            token = first_token(line)
            data = tail(line)
            if token == 'newmtl':
                if current:
                    self.materials.append(current)
                current = Material(name=data)
                print(f"New material: {data}")
            elif not current:
                continue
            elif token == 'Ka':
                current.Ka = Vector3(*map(float, data.split()))
            elif token == 'Kd':
                current.Kd = Vector3(*map(float, data.split()))
            elif token == 'Ks':
                current.Ks = Vector3(*map(float, data.split()))
            elif token == 'Ns':
                current.Ns = float(data)
            elif token == 'Ni':
                current.Ni = float(data)
            elif token == 'd':
                current.d = float(data)
            elif token == 'illum':
                current.illum = int(data)
            elif token == 'map_Ka':
                current.map_Ka = data
            elif token == 'map_Kd':
                current.map_Kd = data
            elif token == 'map_Ks':
                current.map_Ks = data
            elif token == 'map_Ns':
                current.map_Ns = data
            elif token == 'map_d':
                current.map_d = data
            elif token in ('map_bump', 'bump', 'map_Bump'):
                current.map_bump = data
        if current:
            self.materials.append(current)
        file.close()
        print(f"Finished parsing MTL: {path}")
        return True
