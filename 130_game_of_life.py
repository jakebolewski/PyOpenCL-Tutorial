# Display the mandelbrot set

import pyopencl as cl
import numpy
import Tkinter as tk  # XXX What are these three imports?  Why are they here? XXX
import Image          # PIL
import ImageTk        # PIL

w = 1024
h = 1024
# Set the width and height of the window

def calc_fractal(q, maxiter):
    context = cl.create_some_context()
    queue = cl.CommandQueue(context)

    output = numpy.empty(q.shape, dtype=numpy.uint16)

    mf = cl.mem_flags
    q_opencl = cl.Buffer(context, mf.READ_ONLY | mf.COPY_HOST_PTR, hostbuf=q)
    output_opencl = cl.Buffer(context, mf.WRITE_ONLY, output.nbytes)

    program = cl.Program(context, """
    #pragma OPENCL EXTENSION cl_khr_byte_addressable_store : enable
    __kernel void mandelbrot(__global float2 *q,
                     __global ushort *output, ushort const maxiter)
    {
        int gid = get_global_id(0);
        float nreal, real = 0;
        float imag = 0;

        output[gid] = 0;

        for(int curiter = 0; curiter < maxiter; curiter++) {
            nreal = real*real - imag*imag + q[gid].x;
            imag = 2* real*imag + q[gid].y;
            real = nreal;

            if (real*real + imag*imag > 4.0f)
                 output[gid] = curiter;
        }
    }
    """).build()

    program.mandelbrot(queue, output.shape, None, q_opencl,
            output_opencl, numpy.uint16(maxiter))

    cl.enqueue_copy(queue, output, output_opencl).wait()

    return output

def draw(x1, x2, y1, y2, maxiter=30):
    xx = numpy.arange(x1, x2, (x2-x1)/w)
    yy = numpy.arange(y2, y1, (y1-y2)/h) * 1j
    q = numpy.ravel(xx+yy[:, numpy.newaxis]).astype(numpy.complex64)
    output = calc_fractal(q, maxiter)
    mandel = (output.reshape((h,w)) / float(output.max()) * 255.).astype(numpy.uint8)
    return(mandel)

def create_image():
    mandel = draw(-2.13, 0.77, -1.3, 1.3)
    im = Image.fromarray(mandel)
    im.putpalette(reduce(lambda a,b: a+b, ((i,0,0) for i in range(255))))
    return(im)

def create_label():
    image = ImageTk.PhotoImage(im)
    label = tk.Label(root, image=image)
    label.pack()
    return(label)

root = tk.Tk()
root.title("Mandelbrot Set")
im = create_image()
label = create_label()
root.mainloop()
