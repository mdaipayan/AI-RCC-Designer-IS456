# AI-RCC-Designer-IS456

An educational, Open-Source Python framework for automated building planning, structural analysis, and RCC design based on Indian Standards (IS 456:2000).

## Project Workflow
1. **Site Definition**: Input plot area and local bylaws (setbacks, FSI).
2. **Generative Planning**: AI generates multiple floor plans (Duplex/Residential) optimized for structural grid alignment.
3. **Structural Analysis**: 3D Frame Analysis using Finite Element Methods (FEM).
4. **Member Design**: Automated design of Footings, Columns, Beams, and Slabs per IS 456.
5. **Estimation**: Generation of BOQ (Bill of Quantities) and Bar Bending Schedules (BBS).

## Tech Stack
- **UI**: Streamlit
- **Analysis Engine**: PyNite / OpenSeesPy
- **Optimization**: Genetic Algorithms (PyGAD)
- **Standards**: IS 456:2000, IS 875 (Parts 1-3), IS 1893:2016
