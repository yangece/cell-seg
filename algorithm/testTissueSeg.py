from CellDIVE_Seg import CellDIVESeg
from CellDIVE_IO import CellDIVE_IO
import cv2




# Full tissue segmentation
# imName = './test.TIFF'
imName = './nuc_0_256_img.tif'

CDS = CellDIVESeg()
CDIO = CellDIVE_IO()
img = CDIO.ReadPTiffLevel(imName, [-1])

CDS.loadTissueModel('models/LowResModel.sav')

TS = CDS.ExtractTissue(img[0])

fullTS = CDIO.CreateBigTiffFromTIssueMask(TS, imName)

CDIO.WritePTIff(fullTS, 'FullTissueSeg.tif', revOrder=True)

