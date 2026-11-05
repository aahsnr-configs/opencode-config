#!/usr/bin/env python3
"""Small offline physics fixtures. Checks describe their own limited scope."""
import json
import math
import os
from pathlib import Path
import subprocess
import sys
import tempfile

checks = []
metrics = {}


def check(name, passed, **values):
    checks.append({'name': name, 'passed': bool(passed)})
    metrics[name] = values
    if not passed:
        raise AssertionError(name + ': ' + repr(values))


def execute(command, stdin=None):
    result = subprocess.run(command, input=stdin, text=True, capture_output=True, timeout=300)
    Path('engine.log').open('a').write(json.dumps(command) + '\n' + result.stdout + result.stderr)
    if result.returncode:
        raise RuntimeError('Engine failed: ' + repr(command) + '\n' + result.stderr[-1000:])
    return result.stdout + result.stderr


def analysis():
    import numpy as np
    import sympy as s
    from scipy.integrate import solve_ivp
    from ase import Atoms
    from ase.calculators.lj import LennardJones
    import MDAnalysis as mda
    from pymbar import timeseries
    import jax
    import jax.numpy as jnp
    jax.config.update('jax_enable_x64', True)
    jax_value=jax.jit(lambda x:jnp.sum(x*x))(jnp.array([1.,2.]))
    check('JAX JIT execution',float(jax_value)==5.0,platforms=[d.platform for d in jax.devices()])
    from phonopy import Phonopy
    from phonopy.structure.atoms import PhonopyAtoms
    import pymatgen.core
    import seekpath
    import spglib
    q, v, mass, length, gravity = s.symbols('q v m l g', positive=True)
    lagrangian = mass*length**2*v**2/2 + mass*gravity*length*s.cos(q)
    momentum = s.diff(lagrangian, v)
    hamiltonian = s.simplify(momentum*v-lagrangian)
    check('Legendre transform', s.simplify(hamiltonian-(mass*length**2*v**2/2-mass*gravity*length*s.cos(q))) == 0)
    check('pendulum acceleration', s.simplify(s.diff(lagrangian,q)/s.diff(momentum,v)+gravity*s.sin(q)/length) == 0)
    def verlet(dt):
        x, velocity = 1., 0.
        energies = []
        for _ in range(round(20/dt)):
            velocity -= .5*dt*x
            x += dt*velocity
            velocity -= .5*dt*x
            energies.append((x*x+velocity*velocity)/2)
        return max(abs(e-.5) for e in energies)
    coarse, fine = verlet(.1), verlet(.05)
    check('symplectic oscillator refinement', fine < coarse/3, coarse=coarse, fine=fine)
    def orbit(t,y):
        x,ypos,vx,vy=y
        radius=math.hypot(x,ypos)
        return [vx,vy,-x/radius**3,-ypos/radius**3]
    solution=solve_ivp(orbit,[0,2*math.pi],[1,0,0,1],rtol=1e-10,atol=1e-12)
    angular=solution.y[0]*solution.y[3]-solution.y[1]*solution.y[2]
    check('Kepler angular momentum', solution.success and np.max(abs(angular-1))<1e-8)
    atoms=Atoms('Ar2',positions=[[0,0,0],[1.5,0,0]])
    atoms.calc=LennardJones(rc=3)
    force=atoms.get_forces()[0,0]
    atoms.positions[0,0]+=1e-5
    plus=atoms.get_potential_energy()
    atoms.positions[0,0]-=2e-5
    minus=atoms.get_potential_energy()
    check('ASE force finite difference', abs(force+(plus-minus)/2e-5)<1e-7)
    universe=mda.Universe.empty(2,trajectory=True)
    universe.atoms.positions=[[.1,0,0],[9.9,0,0]]
    from MDAnalysis.lib.distances import distance_array
    distance=distance_array(universe.atoms.positions[:1],universe.atoms.positions[1:],box=[10,10,10,90,90,90])[0,0]
    check('periodic minimum image', abs(distance-.2)<1e-5, distance=float(distance))
    rng=np.random.default_rng(42)
    inefficiency=timeseries.statistical_inefficiency(rng.normal(size=5000))
    check('independent sample inefficiency', 1<=inefficiency<2, inefficiency=float(inefficiency))
    crystal=PhonopyAtoms(symbols=['Si','Si'],cell=np.eye(3)*5,scaled_positions=[[0,0,0],[.5,.5,.5]])
    phonon=Phonopy(crystal,supercell_matrix=np.eye(3,dtype=int),primitive_matrix=np.eye(3))
    fc=np.zeros((2,2,3,3))
    fc[0,0]=fc[1,1]=np.eye(3)
    fc[0,1]=fc[1,0]=-np.eye(3)
    phonon.force_constants=fc
    frequencies=phonon.get_frequencies([0,0,0])
    check('two-atom phonon mode count',len(frequencies)==6 and np.isfinite(frequencies).all())
    check('harmonic acoustic sum rule',np.max(abs(fc.sum(axis=1)))<1e-12)
    check('harmonic acoustic and optical branches',np.max(abs(frequencies[:3]))<1e-5 and np.min(frequencies[3:])>0,frequencies_thz=frequencies.tolist(),limitation='Controlled harmonic fixture; not a material phonon calculation')
    check('cubic symmetry',spglib.get_spacegroup((np.eye(3),[[0,0,0]],[14])).startswith('Pm-3m'))


def preparation():
    from openff.toolkit import Molecule, ForceField
    from rdkit import Chem
    molecule=Molecule.from_smiles('CCO')
    check('ethanol atom count',molecule.n_atoms==9)
    check('ethanol formal charge',sum(atom.formal_charge.m for atom in molecule.atoms)==0)
    ff=ForceField('openff_unconstrained-2.2.1.offxml')
    labels=ff.label_molecules(molecule.to_topology())[0]
    check('force field covers bonds',len(labels['Bonds'])==8,force_field='openff_unconstrained-2.2.1.offxml',charge_method='not assigned in this fixture')


def openmm_case(gpu):
    import numpy as np
    import openmm as mm
    from openmm import unit
    system=mm.System()
    system.addParticle(1.)
    force=mm.CustomExternalForce('0.5*k*x*x')
    force.addGlobalParameter('k',10.)
    force.addParticle(0,[])
    system.addForce(force)
    platform=mm.Platform.getPlatformByName('CUDA' if gpu else 'CPU')
    def build(dt, selected):
        integrator=mm.VerletIntegrator(dt)
        context=mm.Context(system,integrator,selected,{'Precision':'mixed'} if selected.getName()=='CUDA' else {})
        context.setPositions([[.2,0,0]])
        context.setVelocities([[0,0,0]])
        return context,integrator
    context,integrator=build(.001,platform)
    state=context.getState(getForces=True,getEnergy=True)
    measured=state.getForces(asNumpy=True).value_in_unit(unit.kilojoule_per_mole/unit.nanometer)[0,0]
    check('harmonic force',abs(measured+2)<1e-5,force=float(measured),platform=context.getPlatform().getName())
    errors=[]
    for dt in (.002,.001):
        ctx,stepper=build(dt,platform)
        initial=ctx.getState(getEnergy=True)
        e0=(initial.getPotentialEnergy()+initial.getKineticEnergy()).value_in_unit(unit.kilojoule_per_mole)
        stepper.step(round(.2/dt))
        state=ctx.getState(getEnergy=True)
        energy=(state.getPotentialEnergy()+state.getKineticEnergy()).value_in_unit(unit.kilojoule_per_mole)
        errors.append(abs(energy-e0))
        del ctx,stepper
    check('NVE timestep refinement',errors[1]<errors[0]*.6+1e-7,errors=errors)
    checkpoint=context.createCheckpoint()
    integrator.step(10)
    expected=context.getState(getPositions=True).getPositions(asNumpy=True).value_in_unit(unit.nanometer)
    context.loadCheckpoint(checkpoint)
    integrator.step(10)
    actual=context.getState(getPositions=True).getPositions(asNumpy=True).value_in_unit(unit.nanometer)
    check('checkpoint continuity',np.allclose(actual,expected,rtol=1e-7,atol=1e-8))
    if gpu:
        cpu,step=build(.001,mm.Platform.getPlatformByName('CPU'))
        reference=cpu.getState(getForces=True).getForces(asNumpy=True).value_in_unit(unit.kilojoule_per_mole/unit.nanometer)[0,0]
        check('CPU CUDA force agreement',abs(reference-measured)<1e-5)


def gromacs(gpu):
    import numpy as np
    Path('argon.gro').write_text('Two argon atoms\n2\n    1ARG     AR    1   1.000   1.000   1.000\n    2ARG     AR    2   1.400   1.000   1.000\n   3.00000   3.00000   3.00000\n')
    Path('topol.top').write_text('[ defaults ]\n1 2 no 1 1\n[ atomtypes ]\nAR 18 39.948 0 A 0.34 0.997\n[ moleculetype ]\nARG 1\n[ atoms ]\n1 AR 1 ARG AR 1 0 39.948\n[ system ]\nArgon pair\n[ molecules ]\nARG 2\n')
    Path('plumed.dat').write_text('d: DISTANCE ATOMS=1,2\nr: RESTRAINT ARG=d AT=0.2 KAPPA=10\nPRINT ARG=d,r.bias FILE=COLVAR STRIDE=1\n')
    Path('run.mdp').write_text('integrator=md\ndt=0.0005\nnsteps=20\nnstenergy=1\nnstcalcenergy=1\ncutoff-scheme=Verlet\nnstlist=10\nrlist=0.9\nrvdw=0.9\nrcoulomb=0.9\ncoulombtype=Cut-off\nvdw-modifier=Potential-shift\npbc=xyz\ngen-vel=no\nconstraints=none\n')
    execute(['gmx','grompp','-f','run.mdp','-c','argon.gro','-p','topol.top','-o','run.tpr'])
    execute(['gmx','mdrun','-s','run.tpr','-deffnm','run','-ntmpi','1','-ntomp','2','-nb','gpu' if gpu else 'cpu','-plumed','plumed.dat'])
    data=np.loadtxt('COLVAR')
    check('PLUMED pair distance',abs(np.atleast_2d(data)[0,1]-.4)<1e-6)
    check('PLUMED harmonic bias',abs(np.atleast_2d(data)[0,2]-.2)<1e-5)
    execute(['gmx','energy','-f','run.edr','-o','energy.xvg'],stdin='Potential\n0\n')
    energy=np.loadtxt('energy.xvg',comments=['#','@'])
    lj=lambda r:4*.997*((.34/r)**12-(.34/r)**6)
    expected=lj(.4)-lj(.9)
    check('LJ pair potential',abs(energy[0,1]-expected)<2e-4,observed=float(energy[0,1]),expected=expected)
    if gpu:
        log=Path('run.log').read_text()
        check('GROMACS GPU offload reported','GPU' in log and ('nonbonded' in log.lower() or 'non-bonded' in log.lower()))
    execute(['gmx','mdrun','-s','run.tpr','-deffnm','run','-cpi','run.cpt','-nsteps','30','-ntmpi','1','-ntomp','2','-nb','gpu' if gpu else 'cpu','-plumed','plumed.dat','-noappend'])
    check('GROMACS checkpoint restart',Path('run.cpt').is_file())


def lammps(gpu):
    import numpy as np
    Path('plumed.dat').write_text('UNITS LENGTH=A ENERGY=eV TIME=ps\nd: DISTANCE ATOMS=1,2\nr: RESTRAINT ARG=d AT=1 KAPPA=2\nPRINT ARG=d,r.bias FILE=COLVAR STRIDE=1\n')
    script='''units metal
atom_style atomic
boundary p p p
region box block 0 10 0 10 0 10
create_box 1 box
create_atoms 1 single 4 5 5
create_atoms 1 single 5.5 5 5
mass 1 39.948
pair_style lj/cut 3
pair_coeff 1 1 0.01 1
neighbor 0.3 bin
fix cv all plumed plumedfile plumed.dat outfile plumed.log
fix dynamics all nve
thermo 1
timestep 0.0001
run 0
write_dump all custom forces.dump id x fx modify sort id
run 10
write_restart restart.bin
'''
    Path('in.lj').write_text(script)
    prefix=['lmp']+(['-k','on','g','1','-sf','kk','-pk','kokkos','gpu/aware','off'] if gpu else [])
    output=execute(prefix+['-in','in.lj'])
    lines=Path('forces.dump').read_text().split('ITEM: ATOMS id x fx\n')[1].strip().splitlines()
    force=float(lines[0].split()[2])
    expected=-24*.01*(2/1.5**13-1/1.5**7)+1.0
    check('LAMMPS analytic LJ plus restraint force',abs(force-expected)<1e-7,observed=force,expected=expected)
    cv=np.loadtxt('COLVAR')
    check('LAMMPS PLUMED pair distance',abs(np.atleast_2d(cv)[0,1]-1.5)<1e-8)
    check('LAMMPS PLUMED harmonic bias',abs(np.atleast_2d(cv)[0,2]-.25)<1e-7)
    check('LAMMPS restart output',Path('restart.bin').stat().st_size>0)
    if gpu:
        check('KOKKOS CUDA enabled','KOKKOS' in output.upper() and ('GPU' in output.upper() or 'CUDA' in output.upper()))


def hoomd_case(gpu):
    import numpy as np
    import hoomd
    def compute(device):
        sim=hoomd.Simulation(device=device,seed=42)
        snapshot=hoomd.Snapshot()
        snapshot.configuration.box=[10,10,10,0,0,0]
        snapshot.particles.N=2
        snapshot.particles.types=['A']
        snapshot.particles.position[:]=[[-.75,0,0],[.75,0,0]]
        sim.create_state_from_snapshot(snapshot)
        pair=hoomd.md.pair.LJ(nlist=hoomd.md.nlist.Cell(buffer=.3),default_r_cut=3.)
        pair.params[('A','A')]={'epsilon':1.,'sigma':1.}
        sim.operations.integrator=hoomd.md.Integrator(dt=.001,methods=[hoomd.md.methods.ConstantVolume(filter=hoomd.filter.All())],forces=[pair])
        sim.run(0)
        forces=pair.forces.copy()
        sim.run(10)
        return forces
    force=compute(hoomd.device.GPU() if gpu else hoomd.device.CPU())
    expected=-24*(2/1.5**13-1/1.5**7)
    check('HOOMD analytic LJ force',abs(force[0,0]-expected)<1e-5)
    if gpu:
        check('HOOMD CPU GPU agreement',np.allclose(force,compute(hoomd.device.CPU()),atol=1e-5))


def quantum():
    import numpy as np
    import qutip as qt
    from tenpy.models.spins import SpinChain
    from tenpy.networks.mps import MPS
    from tenpy.algorithms import dmrg
    times=np.linspace(0,2*np.pi,101)
    evolution=qt.sesolve(.5*qt.sigmax(),qt.basis(2,0),times,e_ops=[qt.sigmaz()])
    check('two level Rabi oscillation',np.max(abs(evolution.expect[0]-np.cos(times)))<2e-5)
    density=qt.mesolve(.5*qt.sigmax(),qt.ket2dm(qt.basis(2,0)),times,c_ops=[.1*qt.sigmam()])
    check('density matrix trace',max(abs(state.tr()-1) for state in density.states)<1e-8)
    check('density matrix positivity',min(min(state.eigenenergies()) for state in density.states)>-1e-6)
    model=SpinChain({'L':4,'S':.5,'Jx':1.,'Jy':1.,'Jz':1.,'bc_MPS':'finite','conserve':None})
    psi=MPS.from_product_state(model.lat.mps_sites(),['up','down','up','down'],bc='finite')
    result=dmrg.run(psi,model,{'mixer':True,'max_sweeps':10,'trunc_params':{'chi_max':16,'svd_min':1e-12}})
    # Four-site open antiferromagnetic spin-1/2 Heisenberg chain.
    ground=-(3+2*math.sqrt(3))/4
    check('DMRG finite chain reference',abs(result['E']-ground)<1e-8,energy=float(result['E']),reference=ground)


def kwant_case():
    import kwant
    lat=kwant.lattice.chain(norbs=1)
    system=kwant.Builder()
    for i in range(4):
        system[lat(i)]=0
    system[lat.neighbors()]=-1
    lead=kwant.Builder(kwant.TranslationalSymmetry((-1,)))
    lead[lat(0)]=0
    lead[lat.neighbors()]=-1
    system.attach_lead(lead)
    system.attach_lead(lead.reversed())
    transmission=kwant.smatrix(system.finalized(),energy=.2).transmission(1,0)
    check('clean chain transmission',abs(transmission-1)<1e-10,transmission=float(transmission))


def pyscf_case():
    from pyscf import gto,scf
    def energy(distance):
        molecule=gto.M(atom=f'H 0 0 0; H 0 0 {distance}',basis='sto-3g',unit='Bohr',verbose=0)
        method=scf.RHF(molecule)
        method.conv_tol=1e-12
        value=method.kernel()
        check('SCF converged at '+str(distance),method.converged)
        return value,method
    value,method=energy(1.4)
    check('H2 minimal basis reference',abs(value+1.116714325)<1e-7,energy_hartree=float(value))
    gradient=method.nuc_grad_method().kernel()[1,2]
    plus,_=energy(1.4001)
    minus,_=energy(1.3999)
    check('SCF force finite difference',abs(gradient-(plus-minus)/.0002)<1e-5)


def qe():
    energies=[]
    for cutoff in (20,30,40):
        Path('si.in').write_text(f'''&CONTROL calculation='scf', prefix='si', pseudo_dir='/opt', outdir='./scratch' /
&SYSTEM ibrav=2, celldm(1)=10.26, nat=2, ntyp=1, ecutwfc={cutoff} /
&ELECTRONS conv_thr=1.0d-9 /
ATOMIC_SPECIES
Si 28.085 Si.pbe-rrkj.UPF
ATOMIC_POSITIONS alat
Si 0 0 0
Si 0.25 0.25 0.25
K_POINTS automatic
2 2 2 0 0 0
''')
        output=execute(['pw.x','-in','si.in'])
        import re
        values=re.findall(r'!\s+total energy\s+=\s+([-\d.]+)',output)
        check('QE SCF convergence '+str(cutoff),'convergence has been achieved' in output and 'JOB DONE' in output and bool(values))
        energies.append(float(values[-1]))
    check('plane wave cutoff refinement',abs(energies[-1]-energies[-2])<.01,energies_ry=energies,tolerance_ry=.01,
          limitation='Small fixture convergence trend; not a converged material prediction')


def cp2k():
    candidates=[Path('/opt/physics/share/cp2k/data'),Path('/opt/physics/share/cp2k'),Path('/opt/physics/data'),Path('/usr/share/cp2k/data'),Path('/usr/share/cp2k')]
    data=next((p for p in candidates if (p/'BASIS_MOLOPT').is_file()),None)
    if data is None:
        raise RuntimeError('CP2K basis/potential data missing')
    Path('h2.inp').write_text(f'''&GLOBAL
 PROJECT h2
 RUN_TYPE ENERGY_FORCE
 PRINT_LEVEL LOW
&END GLOBAL
&FORCE_EVAL
 METHOD Quickstep
 &DFT
  BASIS_SET_FILE_NAME {data}/BASIS_MOLOPT
  POTENTIAL_FILE_NAME {data}/GTH_POTENTIALS
  &MGRID
   CUTOFF 200
  &END MGRID
  &SCF
   EPS_SCF 1.0E-8
   MAX_SCF 100
  &END SCF
  &XC
   &XC_FUNCTIONAL PBE
   &END XC_FUNCTIONAL
  &END XC
 &END DFT
 &PRINT
  &FORCES ON
  &END FORCES
 &END PRINT
 &SUBSYS
  &CELL
   ABC 10 10 10
  &END CELL
  &COORD
   H 5 5 4.63
   H 5 5 5.37
  &END COORD
  &KIND H
   BASIS_SET DZVP-MOLOPT-SR-GTH
   POTENTIAL GTH-PBE-q1
  &END KIND
 &END SUBSYS
&END FORCE_EVAL
''')
    import shutil
    executable=next((p for p in ('cp2k.psmp','cp2k.ssmp','cp2k') if shutil.which(p)),None)
    if executable is None:
        raise RuntimeError('CP2K executable missing')
    output=execute([executable,'-i','h2.inp'])
    check('CP2K SCF convergence','SCF run converged' in output and 'ENERGY|' in output)
    check('CP2K force output','ATOMIC FORCES' in output or bool(list(Path('.').glob('*frc*'))))


def pymbar_case(gpu):
    import numpy as np
    import jax
    from pymbar import MBAR
    devices=jax.devices()
    check('JAX CUDA device selected',gpu and jax.default_backend()=='gpu' and any(d.platform=='gpu' for d in devices),
          devices=[str(d) for d in devices],backend=jax.default_backend())
    u_kn=np.array([[0.,1.,0.,1.],[1.,0.,1.,0.]],dtype=np.float64)
    mbar=MBAR(u_kn,np.array([2,2]))
    delta=mbar.compute_free_energy_differences()['Delta_f'][0,1]
    check('PyMBAR JAX free energy',np.isfinite(delta) and abs(delta)<1e-6,delta_f=float(delta))


def main():
    profile=sys.argv[1]
    gpu=profile.endswith('-cuda')
    key=profile.removesuffix('-cuda')
    functions={'analysis':analysis,'pymbar':lambda:pymbar_case(gpu),'preparation':preparation,'openmm':lambda:openmm_case(gpu),
               'gromacs':lambda:gromacs(gpu),'lammps':lambda:lammps(gpu),'hoomd':lambda:hoomd_case(gpu),
               'quantum':quantum,'kwant':kwant_case,'pyscf':pyscf_case,'qe':qe,'cp2k':cp2k}
    def perform():
        try:
            functions[key]()
        finally:
            Path('experiment.json').write_text(json.dumps({'profile':profile,'checks':checks,'metrics':metrics,
                'limitations':['Small deterministic fixture; scientific applicability requires problem-specific convergence and uncertainty analysis.']},indent=2,allow_nan=False)+'\n')
    if '--smoke' in sys.argv:
        with tempfile.TemporaryDirectory() as tmp:
            os.chdir(tmp)
            perform()
    else:
        perform()
    return 0


if __name__=='__main__':
    sys.exit(main())
