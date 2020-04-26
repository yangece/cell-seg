from CellDIVE_Seg import CellDIVESeg
from CellDIVE_IO import CellDIVE_IO
import cv2
import time



# Full tissue segmentation
imName = './nuc_0_256_img.tif'
tsSegName = 'FullTissueSeg.tif'

CDS = CellDIVESeg()
CDIO_ts = CellDIVE_IO()
CDIO_dp = CellDIVE_IO()

tsSeg = CDIO_ts.ReadPTiffLevel(tsSegName, [0])
dpIM = CDIO_ts.ReadPTiffLevel(imName, [0])

t1 = time.time()
print('Start prediction')
DS = CDS.mlNucSeg(dpIM[0], 200, tsSeg[0], modelfName='models/unet_models/nuc_seg_unet_model_48_sp.h5')
t2 = time.time()
print('Prediction time:', t2-t1)

print(DS)

cv2.imwrite('FullDAPISegDL48_r9v6.tif',DS.astype('uint8'))
# CDIO_dp.WritePTIff([DS], 'FullDAPISegDL48.tif', revOrder=False) #(x=3900,y=11100)



