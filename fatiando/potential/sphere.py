r"""
Calculate the potential fields of a homogeneous sphere.

**Magnetic**

Calculates the total field anomaly. Uses the formula in Blakely (1995).

* :func:`~fatiando.potential.sphere.tf`: calculates the total-field anomaly

Remember that:

The magnetization :math:`\mathbf{M}` and the dipole moment :math:`\mathbf{m}`
are related with the volume V:

.. math::

    \mathbf{M} = \dfrac{\mathbf{m}}{V}.

The total-field anomaly is:

.. math::

    \Delta T = |\mathbf{T}| - |\mathbf{F}|,

where :math:`\mathbf{T}` is the measured field and :math:`\mathbf{F}` is a
reference (regional) field. The forward modeling functions
:func:`~fatiando.potential.sphere.bx`, :func:`~fatiando.potential.sphere.by`,
and :func:`~fatiando.potential.sphere.bz` calculate the 3 components of the
field perturbation :math:`\Delta\mathbf{F}`

.. math::

    \Delta\mathbf{F} = \mathbf{T} - \mathbf{F}.

Then the total-field anomaly caused by the sphere is

.. math::

    \Delta T \approx \hat{\mathbf{F}}\cdot\Delta\mathbf{F}.


**Gravity**



**References**


----
"""
import numpy
from numpy import pi

from fatiando.constants import SI2EOTVOS, SI2MGAL, G, CM, T2NT


def _dircos(inc, dec):
    """
    Returns the 3 coordinates of the unit vector given its inclination and
    declination.

    Parameter:

    * inc : float
        The inclination of the regional field (in degrees)
    * dec : float
        The declination of the regional field (in degrees)

    Returns:

    * vect : list = [x, y, z]
        The unit vector
        
    """
    d2r = pi/180.
    vect = [numpy.cos(d2r*inc)*numpy.cos(d2r*dec),
            numpy.cos(d2r*inc)*numpy.sin(d2r*dec),
            numpy.sin(d2r*inc)]
    return vect

def tf(xp, yp, zp, spheres, inc, dec):
    """
    Calculate the total-field anomaly of spheres.

    .. note:: Input units are SI. Output is in nT

    Parameters:

    * xp, yp, zp : arrays
        The x, y, and z coordinates where the anomaly will be calculated
    * spheres : list of :class:`fatiando.mesher.ddd.Sphere`
        The spheres. Spheres must have the properties ``'magnetization'``,
        ``'inclination'`` and ``'declination'``. If ``'inclination'`` and
        ``'declination'`` are not present, will use the values of *inc* and
        *dec* instead. Those without ``'magnetization'`` will be ignored.
    * inc : float
        The inclination of the regional field (in degrees)
    * dec : float
        The declination of the regional field (in degrees)

    Returns:

    * tf : array
        The total-field anomaly
        
    """
    if xp.shape != yp.shape != zp.shape:
        raise ValueError("Input arrays xp, yp, and zp must have same shape!")
    tf = numpy.zeros_like(xp)
    # Calculate the 3 components of the unit vector in the direction of the
    # regional field
    fx, fy, fz = _dircos(inc, dec)
    for sphere in spheres:
        if sphere is None or 'magnetization' not in sphere.props:
            continue
        radius = sphere.radius
        mag = sphere.props['magnetization']
        inclination = inc
        declination = dec
        # The 3 components of the unit vector in the direction of the
        # magnetization
        mx, my, mz = fx, fy, fz
        if 'inclination' in sphere.props and 'declination' in sphere.props:
            inclination = sphere.props['inclination']
            declination = sphere.props['declination']
            mx, my, mz = _dircos(inclination, declination)
        # First thing to do is make the computation point P the origin of the
        # coordinate system
        x = xp - sphere.x
        y = yp - sphere.y
        z = zp - sphere.z
        # Calculate the 3 components of B
        dotprod = mx*x + my*y + mz*z
        r_sqr = x**2 + y**2 + z**2
        r5 = r_sqr**(2.5)
        moment = mag*4.*pi*(radius**3)/3.
        bx = moment*(3*dotprod*x - r_sqr*mx)/r5
        by = moment*(3*dotprod*y - r_sqr*my)/r5
        bz = moment*(3*dotprod*z - r_sqr*mz)/r5        
        tf = tf + (fx*bx + fy*by + fz*bz)
    return CM*T2NT*tf

def gz(xp, yp, zp, spheres):
    """
    Calculates the :math:`g_z` gravity acceleration component.

    .. note:: The coordinate system of the input parameters is to be x -> North,
        y -> East and z -> Down.

    .. note:: All input values in SI and output in mGal!

    Parameters:
    
    * xp, yp, zp : arrays
        The x, y, and z coordinates where the field will be calculated
    * spheres : list of :class:`fatiando.mesher.ddd.Sphere`
        The spheres. Spheres must have the property ``'density'``. Those without
        will be ignored.

    Returns:
    
    * res : array
        The field calculated on xp, yp, zp
        
    """
    
    if xp.shape != yp.shape != zp.shape:
        raise ValueError("Input arrays xp, yp, and zp must have same shape!")
    res = numpy.zeros_like(xp)
    for sphere in spheres:
        if sphere is None or 'density' not in sphere.props:
            continue
        radius = sphere.radius
        density = sphere.props['density']
        # First thing to do is make the computation point P the origin of the
        # coordinate system
        x = xp - sphere.x
        y = yp - sphere.y
        z = zp - sphere.z
        r_cb = (x**2 + y**2 + z**2)**(1.5)
        mass = density*4.*pi*(radius**3)/3.
        res = res + mass*z/r_cb
    return G*SI2MGAL*res
