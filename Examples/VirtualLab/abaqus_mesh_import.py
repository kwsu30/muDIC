# This allows for running the example when the repo has been cloned
import sys
from os.path import abspath

sys.path.extend([abspath(".")])

# Example code follows
import logging
import numpy as np
import matplotlib.pyplot as plt
import muDIC.vlab as vlab
import muDIC as dic


"""
This example case runs an experiment where a deformation gradient is used
to deform a synthetically generated speckle, the speckle is then down sampled by a factor of four
and sensor artifacts are included.

The analysis is then performed and the resulting deformation gradient field is compared to the
one used to deform the images
"""





mesh = dic.mesh_from_abaqus('./abaqusMeshes/ring.inp', unit_dim=True)
mesh.center_mesh_at(3000,3000)
mesh.scale_mesh_x(1500)
mesh.scale_mesh_y(1500)


# Set the amount of info printed to terminal during analysis
logging.basicConfig(format='%(name)s:%(levelname)s:%(message)s', level=logging.INFO)
show_results = False

# Define the image you want to analyse
n_imgs = 2
image_shape = (4000, 4000)
downsample_factor = 1
super_image_shape = tuple(dim * downsample_factor for dim in image_shape)

# Make a speckle image
speckle_image = vlab.rosta_speckle(super_image_shape, dot_size=1, density=0.5, smoothness=2.0)

displacement_function = vlab.deformation_fields.harmonic_bilat

# Make an image deformed
image_deformer = vlab.imageDeformer_from_uFunc(displacement_function, omega=2 * np.pi / (500. * downsample_factor),
                                               amp=2.0 * downsample_factor)

# Make an image down-sampler including downscaling, fill-factor and sensor grid irregularities
downsampler = vlab.Downsampler(image_shape=super_image_shape, factor=downsample_factor, fill=.95,
                               pixel_offset_stddev=0.05)

# Make a noise injector producing 2% gaussian additive noise
noise_injector = vlab.noise_injector("gaussian", sigma=.02)

# Make an synthetic image generation pipeline
image_generator = vlab.SyntheticImageGenerator(speckle_image=speckle_image, image_deformer=image_deformer,
                                               downsampler=downsampler, noise_injector=noise_injector, n=n_imgs)
# Put it into an image stack
image_stack = dic.ImageStack(image_generator)

# Prepare the analysis input and initiate the analysis
input = dic.DICInput(mesh, image_stack)
input.tol = 1e-6
input.interpolation_order = 4

dic_job = dic.DICAnalysis(input)
results = dic_job.run()

# Calculate the fields for later use. Seed is used when spline elements are used and upscale is used for Q4.
fields = dic.Fields(results, seed=101, upscale=False)



def showMeshPlot(nodes, elements, values):
    # From here: https://stackoverflow.com/questions/52202014/how-can-i-plot-2d-fem-results-using-matplotlib
    import matplotlib

    y = nodes[:, 0]
    z = nodes[:, 1]

    def quatplot(y, z, quatrangles, values, ax=None, **kwargs):
        if not ax: ax = plt.gca()
        yz = np.c_[y, z]
        verts = yz[quatrangles]
        pc = matplotlib.collections.PolyCollection(verts, **kwargs)
        pc.set_array(values)
        ax.add_collection(pc)
        ax.autoscale()
        return pc

    fig, ax = plt.subplots()
    ax.set_aspect('equal')

    pc = quatplot(y, z, np.asarray(elements), values, ax=ax,
                  edgecolor="crimson", cmap="rainbow", linewidth=0)
    fig.colorbar(pc, ax=ax)
    # ax.plot(y,z, marker="o", ls="", color="crimson")

    ax.set(title='This is the plot for: quad', xlabel='Y Axis', ylabel='Z Axis')

    plt.show()


nodes = np.array([mesh.xnodes, mesh.ynodes]).transpose()
elements = mesh.ele.transpose()
stresses = fields.disp()[:, 0, 0, 0, -1]

plt.imshow(image_stack[0], cmap=plt.cm.gray)
showMeshPlot(nodes, elements, stresses)
