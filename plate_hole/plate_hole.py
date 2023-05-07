#!/usr/bin/env python
# coding: utf-8
################################################################
import subprocess
import matplotlib.tri as tri
import matplotlib.pyplot as plt
import numpy as np
import akantu as aka
import solidipes as sp
import os
import streamlit as st
import argparse
from contextlib import contextmanager
plt.rcParams['figure.figsize'] = [10, 10]
################################################################


@contextmanager
def make_figure():

    fig = plt.figure()
    axe = fig.add_subplot(111)
    axe.set_aspect('equal')
    try:
        yield fig, axe
    finally:
        st.pyplot(fig)


################################################################
dirname = os.path.dirname(__file__)

params = {
    'w': 10.,           # width (x-axis)
    'l': 5.,            # length (y-axis)
    'h1': 0.01,         # characteristic mesh size at the hole
    'h2': 0.3,          # characteristic mesh size in corners
    'R': 2.,            # radius of the hole
    'traction': 10,     # radius of the hole
    'rho': 7800,
    'E': 2.1e11,
    'nu': 0.3
}

col1, col2 = st.columns(2)

with col1:
    f = sp.load_file(os.path.join(dirname, 'plate-hole-2.svg'))
    f.view()

for p, value in params.items():
    _type = type(value)
    val = col2.text_input(p, value=value, key=p+dirname)
    params[p] = _type(val)


def create_model(**params):
    inp = argparse.Namespace(**params)
    material_file = f"""
    material elastic [
        name = steel
        rho = {inp.rho}    # density
        E   = {inp.E}      # young's modulus
        nu  = {inp.nu}     # poisson's ratio
    ]"""
    # writing the material file
    open('material.dat', 'w').write(material_file)
    # reading the material file
    material_file = 'material.dat'
    aka.parseInput(material_file)

    # geometric parameters
    mesh_file = f"""
    Point(1) = {{0, 0, 0, {inp.h2} }};
    Point(2) = {{ {inp.R}, 0, 0, {inp.h1} }};
    Point(3) = {{ {inp.w}, 0, 0, {inp.h2} }};
    Point(4) = {{ {inp.w}, {inp.l}, 0, {inp.h2} }};
    Point(5) = {{ 0,   {inp.l}, 0, {inp.h2} }};
    Point(6) = {{0,    {inp.R}, 0, {inp.h1} }};
    """

    mesh_file += """
    Circle(1) = {6, 1, 2};
    Line(2) = {2, 3};
    Line(3) = {3, 4};
    Line(4) = {4, 5};
    Line(5) = {5, 6};
    Line Loop(6) = {1, 2, 3, 4, 5};
    Plane Surface(7) = {6};
    """

    mesh_file += """
    Physical Surface(8) = {7};
    Physical Line("XBlocked") = {5};
    Physical Line("YBlocked") = {2};
    Physical Line("Traction") = {3};
    """

    open('plate.geo', 'w').write(mesh_file)

    ret = subprocess.run("gmsh -2 -order 1 -o plate.msh plate.geo", shell=True)
    if ret.returncode:
        print("Beware, gmsh could not run: mesh is not regenerated")
    else:
        print("Mesh generated")

    # reading the mesh
    spatial_dimension = 2
    mesh_file = 'plate.msh'
    mesh = aka.Mesh(spatial_dimension)
    mesh.read(mesh_file)
    # creating the solid mechanics model
    model = aka.SolidMechanicsModel(mesh)

    # initialize a static solver
    model.initFull(_analysis_method=aka._static)

    # set the displacement/Dirichlet boundary conditions
    model.applyBC(aka.FixedValue(0.0, aka._x), "XBlocked")
    model.applyBC(aka.FixedValue(0.0, aka._y), "YBlocked")

    # set the force/Neumann boundary conditions
    model.getExternalForce()[:] = 0

    trac = [inp.traction, 0]  # Newtons/m^2

    model.applyBC(aka.FromTraction(trac), "Traction")

    # configure the linear algebra solver
    solver = model.getNonLinearSolver()
    solver.set("max_iterations", 2)
    solver.set("threshold", 1e-10)
    solver.set("convergence_type", aka.SolveConvergenceCriteria.residual)

    # compute the solution
    model.solveStep()

    return model, mesh


button = st.button('Compute!', key='button'+dirname)

if button:
    model, mesh = create_model(**params)
    # extract the mesh
    conn = mesh.getConnectivity(aka._triangle_3)
    nodes = mesh.getNodes()
    triangles = tri.Triangulation(nodes[:, 0], nodes[:, 1], conn)
    u = model.getDisplacement()
    stress_field = model.getMaterial(0).getStress(aka._triangle_3)

    # plot the result
    with make_figure() as (fig, axe):
        # plots the pristine state
        t = axe.triplot(triangles, '--', lw=.8)

    with make_figure() as (fig, axe):
        t = axe.triplot(triangles, '--', lw=.8)
        t = axe.triplot(
            nodes[:, 0]+u[:, 0],
            nodes[:, 1] + u[:, 1], triangles=conn)

    with make_figure() as (fig, axe):

        # plot displacement field
        u_disp = axe.tricontourf(triangles, np.linalg.norm(u, axis=1))
        t = axe.triplot(triangles, '--', lw=.8)

        cbar = fig.colorbar(u_disp, location='top')
        cbar.set_label('displacement magnitude [m]')

    with make_figure() as (fig, axe):
        stress_disp = axe.tripcolor(
            triangles, np.linalg.norm(stress_field, axis=1))
        cbar = fig.colorbar(stress_disp, location='top')
        cbar.set_label('stress magnitude [Pa]')