# FEALinkMaterial
# Ryan Arata
# updated Apr 2016
#
# This module implements the Material class

class Material(object):
    def __str__(self):
        output = "Material __str__ function not yet implemented"
        return output
        numstr = str(self.number)
        modstr = '%.5g' % self.modulus
        areastr = '%.5g' % self.area
        poisstr = str(self.poissonratio)

        output = numstr + "\t" + modstr
        if len(modstr) > 5:
            output += "\t" + areastr
        else:
            output += "\t\t" + areastr

        if len(areastr) > 5:
            output += "\t" +poisstr
        else:
            output += "\t\t" + poisstr

        return output

    def __init__(self,num,E,A,density=0):
        self.number = num
        self.modulus = E
        self.area = A
        self.density = density
