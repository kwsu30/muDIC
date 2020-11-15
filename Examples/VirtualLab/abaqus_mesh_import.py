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
This example imports a mesh from an input-file generated by Abaqus.
A speckled image is generated and deformed according to a bi-harmonic displacement field and the results
are plotted using a rudimentary visualization tool.
"""

mesh = dic.mesh_from_abaqus('./abaqusMeshes/ring.inp', unit_dim=True)

# You can move the mesh to the desired position like this
mesh = mesh.center_mesh_at(1000, 1000).scale_mesh_x(1800).scale_mesh_y(1800)
# or like this
mesh = mesh.fit_to_box(200, 1800, 200, 1800)

# Set the amount of info printed to terminal during analysis
logging.basicConfig(format='%(name)s:%(levelname)s:%(message)s', level=logging.INFO)
show_results = False

# Define the image you want to analyse
n_imgs = 2
image_shape = (2000, 2000)
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
inputDIC = dic.DICInput(mesh, image_stack)
inputDIC.tol = 1e-6
inputDIC.interpolation_order = 4

dic_job = dic.DICAnalysis(inputDIC)
results = dic_job.run()

fields = dic.Fields(results)

# Show a field
viz = dic.Visualizer(fields,images=image_stack)

# Uncomment the line below to see the results
viz.show(field="displacement", component = (0,0), frame=-1)




#values = fields.disp()[:, 0, 0, 0, -1]

#plt_unstructured_results(mesh.xnodes, mesh.ynodes, mesh.ele.transpose(), values)