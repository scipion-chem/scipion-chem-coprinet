.. |organization| replace:: scipion-chem
.. |repository| replace:: scipion-chem-CoPriNet

========================================
CoPriNet scipion plugin
========================================
**Documentation under development, sorry for the inconvenience**
Scipion framework plugin for the use of CoPriNet software tools.
  
========================================
Install this plugin
========================================
You will need to use `Scipion3 <https://scipion-em.github.io/docs/docs/scipion
-modes/how-to-install.html>`_ to run these protocols.

CoPriNet, is installed automatically by Scipion.

- **Install the stable version**

    Through the plugin manager GUI by launching Scipion and following **Others** >> **Plugin Manager**

    or

.. parsed-literal::

    scipion3 installp -p \ |repository|\ 


- **Developer's version**

    1. Download repository:

    .. parsed-literal::

        git clone \https://github.com/\ |organization|\ /\ |repository|\ .git

    2. Install:

    .. parsed-literal::

        scipion3 installp -p /path/to/\ |repository|\  --devel
  
========================================
Protocols
========================================
This plugin contains the following protocols:

**None for now**

========================================
Packages & enviroments
========================================
Packages installed by this plugin can be located in ``/path/to/scipion/software/em/``.

The following packages will be created:

- CoPriNet-``version``

Where ``version`` is the current version of that specific package.

Also, the following conda enviroments will be created:

- CoPriNet-``version``

As of today, Scipion does not automatically uninstall the conda enviroments created in the installation process when uninstalling a plugin, so keep this list in mind if you want to clean up some disk space if you need to uninstall this one.

========================================
External software
========================================
This plugin integrates the following software:
  
.. _CoPriNet: https://github.com/MolecularAI/CoPriNet
.. |CoPriNet| replace:: **CoPriNet** 

- |CoPriNet|_: Tool for CoPriNet planning.

========================================
Changelog
========================================
All the recent version changes can be found `here <https://github.com/scipion-chem/scipion-chem-CoPriNet/blob/devel/CHANGES.rst>`_.
