# -*- coding: utf-8 -*-
"""
Created on March 10 2020

@authors: Yousef Al-Kofahi
"""

import time
import numpy as np
import cv2
from skimage import feature
from keras.models import model_from_json, Model




#%%
class Traditional_ML():
    def __init__(self):
        self.trainImg = None; # could be a list of images
        self.trainMsk = None; #
        self.labeledImg = None;
         
        self.testImg = None; # could be a list of images
        self.testMsk = None; #
         
        self.write_feats = False
        self.wSize = 5
        self.feats = None
        self.feats_out = None
        self.verbose = False
        self.ratio   = 0.1
        self.classifierType = 1
        self.classificationMode = 1
        #self.neuritePreProcess = 0
        self.MeanFeats = None
        self.image_count = None
        self.numClasses = 2
        self.DLFeats_model = None
        self.DLFeats_model_name = "models/model2"

#%%
    def LoadModelCNNModel(self, modelFName):
        jFname = modelFName.replace('h5','json') 
        
        with open(jFname, 'r') as json_file:
            loaded_model_json = json_file.read()
            json_file.close()
            self.model = model_from_json(loaded_model_json)
            self.model.load_weights(modelFName)
            
            #YK114
            self.DLFeats_model = self.model;

# %%
    def Extract_DL_Features_TF(self, inImg, featsType):
        ###
        ### This is similar to the previous function, but it uses Keras/Tensorflow models instead of MXNet 
        ###
        
        
        s = inImg.shape
        
        # load the model  and define output layer for feature extraction:
        if self.DLFeats_model is None:            
            json_file = open(self.DLFeats_model_name+'.json', 'r')
            loaded_model_json = json_file.read()
            json_file.close()
            self.DLFeats_model = model_from_json(loaded_model_json)
            
            # load weights into new model
            self.DLFeats_model.load_weights(self.DLFeats_model_name+".h5")
            print("Load Default DLFeats_model From from disk")
        else:
            print("DLFeats_model is already loaded")
            
            
        # YK 114: let's get the indexes of the output layers to be used for feature extraction
        inp = -1
        SH = []        
        INDs = []     
        
        for layer in self.DLFeats_model.layers:
            inp+=1 
            if 'conv2d' in layer.name:                
                if len(SH) == 0: 
                    lastIND = inp
                    SH = layer.get_output_at(0).get_shape().as_list()[1:]
                    continue     
                SHtmp = layer.get_output_at(0).get_shape().as_list()[1:]
                if (SHtmp != SH):
                    INDs.append(lastIND)
                    SH = SHtmp
                    if len(INDs) == 2:
                        break
                else:
                    lastIND = inp
        
        indd = INDs[0]
        if featsType == 64:
            indd = INDs[1]
        intermediate_layer_model = Model(inputs=self.DLFeats_model.input,outputs=self.DLFeats_model.get_layer(None,indd).output)

        
        #first, get the shape of the output layer
        sy = intermediate_layer_model.get_input_shape_at(0)[1]
        sx = intermediate_layer_model.get_input_shape_at(0)[2]
        
        # next, we need to define how much overlap and the padding size
        ov = int(np.round(sx/10)) #overlap size
        stp = sx - ov # step size
        ry = range(0,s[0],stp)
        pd1 = ry[-1]+sy-s[0]
        rx = range(0,s[1],stp)
        pd2 = rx[-1]+sx-s[1]
        
        
        im = inImg.copy()   

                  
        if im.max() > 255:
            im = (im/256).astype('uint8')
        im = np.pad(im,((0,pd1),(0,pd2)),'constant',constant_values=0)   
        
        outIM = np.zeros((im.shape[0],im.shape[1], featsType), np.float32)     
        
        # go over the image patches and run prediction
        w = 3
        if featsType == 64:
            w = 7
        print('Extract DL features')
        for i in range(0,s[0],stp):#160):
            for j in range(0,s[1],stp):#160):
                
                #print(i)
                # extract the image patch and create a 4D tensor
                IMG = im[i:i+sy,j:j+sx]
                IMG = np.expand_dims(IMG, axis=0)
                IMG = np.expand_dims(IMG, axis=4)
                
                #print(IMG.shape)
                
                # evaluate loaded model on test data
                intermediate_output = intermediate_layer_model.predict(IMG)
                #print(intermediate_output.shape)
                
                for k in range(0,featsType): 
                    tmp = intermediate_output[0,:,:,k]                   
                    if featsType == 64:
                        tmp = cv2.resize(tmp,(0,0), fx=2.0, fy=2.0, interpolation = cv2.INTER_LINEAR)
                    tmp = tmp[w:-w,w:-w]
                    
                    #outIM[i+w:i+176-w,j+w:j+176-w, k] = np.maximum(outIM[i+w:i+176-w,j+w:j+176-w,k],tmp)
                    outIM[i+w:i+sy-w,j+w:j+sx-w, k] = np.maximum(outIM[i+w:i+sy-w,j+w:j+sx-w,k],tmp)
                    
        
        
        #Feats = np.zeros((outIM[pd1:-pd1,pd2:-pd2,:].shape[0], outIM[pd1:-pd1,pd2:-pd2,:].shape[1],outIM[pd1:-pd1,pd2:-pd2,:].shape[2]),np.float32)
        Feats = np.zeros((outIM[:-pd1,:-pd2,:].shape[0], outIM[:-pd1,:-pd2,:].shape[1],outIM[:-pd1,:-pd2,:].shape[2]),np.float32)
        
        for i in range(0,featsType):
            Feats[:,:,i] = outIM[0:-pd1,0:-pd2,i]                        
            # MXY: uncomment to save feature maps as float images
            # nm = str(i)+'.tiff'
            # img1 = Image.fromarray(Feats[:,:,i])
            # img1.save(nm)
                
        outIM = None
                
            
        print(Feats.shape)    
        if self.verbose:
            print('shape of inImg: ',s)
            print('feature image shape: ', Feats.shape)          

        
        return Feats

    def getFeats_Generic(self, img, wSize=5, verbose=False):
        """
        Computes simple(first and second order statistics) features
    
        Parameters
        ----------
        wSize: int
            number of pixels in the window
    
    
        Outputs
        -------
        3D dataset
        """
        
        start_time = time.time()
        nFeats = 9;
        s = img.shape
        feats = np.zeros((s[0],s[1],nFeats))
        
        i = 0
        # img = img[:,:,0]
        feats[:,:,i] = img
    
        i += 1
        sigma =  wSize/4.0
        feats[:,:,i] = cv2.GaussianBlur(img, (wSize, wSize), sigma)
    
        #compute the laplacian for Gaussian
        #i += 1
        #feats[:,:,i] = cv2.Laplacian(feats[:,:,i-1].astype('float'), cv2.CV_64F)
    
        i += 1
        dWSize = 2*wSize+1
        feats[:,:,i] = cv2.GaussianBlur(img, (dWSize, dWSize), sigma*2)
    
        # difference of gaussians, are very close to Laplacian of gaussian
        i += 1
        feats[:,:,i] = feats[:,:,i-1] - feats[:,:,i-2]
    
        #i += 1
        #feats[:,:,i] = np.abs(feats[:,:,i-1])
    
        i += 1
        kernel = np.ones((int(wSize),int(wSize)),np.uint8)
        feats[:,:,i] = cv2.morphologyEx(feats[:,:,1], cv2.MORPH_TOPHAT, kernel)
    
        i += 1
        feats[:,:,i] = cv2.morphologyEx(feats[:,:,1], cv2.MORPH_BLACKHAT, kernel)
        
        
        i += 1
        feats[:,:,i] = cv2.Laplacian(feats[:,:,i-1].astype('float'), cv2.CV_64F)
        
        
        i += 1
        feats[:,:,i] = feature.local_binary_pattern(img, 24, 4, method="uniform")
        
        
        # HoG image
        # i += 1
        # fd, hog_img = hog(img, orientations=8, pixels_per_cell=(16,16),cells_per_block=(1,1), visualise=True)
        # feats[:,:,i] = hog_img

        # # Frangi vesseness image:
        # i+=1
        # feats[:,:,i]=frangi(img)
    
        #Hessian image
        #i+=1
        #feats[:,:,i]= hessian(img)
    
#         i += 1
#         tmpImg = np.zeros((2,s[0],s[1]), np.uint16)
#         tmpImg[0] = feats[:,:,1]
#         tmpImg[1] = np.ones((s[0],s[1]), np.uint16)
#     
#         feats[:,:,i] = gtk.PunctaEnhancement_1D(tmpImg, 2*wSize)
        
        for j in range(0,i+1):
            feats[:,:,j] = cv2.blur(feats[:,:,j],(wSize,wSize))
    
        end_time = time.time()
    
        if verbose:
            print (' Feature compute time', end_time-start_time)

        return feats;
    
#%%    
    def getX(self, img, msk, wSize=5,  verbose=True, featsType=1, imageType='Neurites'):
  
        """From the image and mask, creates the input X
    
        Parameters
        ----------
        img: arr
            The image
        msk: arr
            A mask representing a given strike
        """
        
        
        if(featsType == 1):            
            if(imageType == 'Neurites'):
                feats = self.getFeats_Neurites(img, wSize, verbose)
            elif (imageType == 'Brightfield'):
                feats = self.getFeats_Brightfield(img, wSize, verbose)
            else:
                feats = self.getFeats_Generic(img, wSize, verbose)
                     
        else:

            # feats = self.Extract_DL_Features(img, featsType)
            feats = self.Extract_DL_Features_TF(img, featsType)

        
        if self.verbose:
            print('feature shape: ', feats.shape)
        
        # Only return features that correspond with label mask:
        idxMsk = np.where(msk>0)
        X = feats[idxMsk[0],idxMsk[1],:]
        
        return (X,idxMsk)
#%%   
    def getY(self, msk, idxMsk):
        """
        """
        Y = msk[idxMsk]
        Y = Y.ravel()
        return Y
#%%    
    #YK1207
    def predict_CNN_pixel_level(self, image):
        #first, get the size of the patch .. for now we will support single channels only
        sy = self.model.get_input_shape_at(0)[1]
        sx = self.model.get_input_shape_at(0)[2]
        
        print('patch size is ',sy,sx)
        
        if sx != sy:
            return 0 # for now let's focus on square patches only
        
        # get the number of outputs (classes)
        OL = self.model.get_config()['output_layers'][0][0]
        nC = self.model.get_layer(OL).get_output_shape_at(0)[3]
        
                
        # next, we need to define how much overlap and the padding size
        ov = int(np.round(sx/10)) #overlap size
        stp = sx - ov # step size
        ry = range(0,image.shape[0],stp)
        pdy = ry[-1]+sy-image.shape[0]
        rx = range(0,image.shape[1],stp)
        pdx = rx[-1]+sx-image.shape[1]
        # then, we convert the image into 8 bit (divide by 256) and pad with zeros
        tmpImg = image.copy()
        #if tmpImg.max() > 255:
        #    tmpImg = tmpImg/256
        tmpImg = tmpImg.astype('uint16')
        tmpImg = np.pad(tmpImg,((0,pdy),(0,pdx)),'constant',constant_values=0)
        
        # initialize the output pred image
        outIM = np.zeros((tmpImg.shape[0], tmpImg.shape[1], nC), np.float32)
        
        # then, go in a loop to run prediction for the patches ,,, one at a time
        print('Run prediction')
        for i in range(0,image.shape[0],stp):
            for j in range(0,image.shape[1],stp):
                # extract the image patch and create a 4D tensor
                IMG = tmpImg[i:i+sy,j:j+sx]
                IMG = np.expand_dims(IMG, axis=0)
                IMG = np.expand_dims(IMG, axis=4)
                
                # evaluate loaded model on test data
                results = self.model.predict(IMG)
                
                outIM[i:i+sy,j:j+sx,0] = np.maximum(outIM[i:i+sy,j:j+sx,0],results[0,:,:,0])
                outIM[i:i+sy,j:j+sx,1] = np.maximum(outIM[i:i+sy,j:j+sx,1],results[0,:,:,1])
                outIM[i:i+sy,j:j+sx,2] = np.maximum(outIM[i:i+sy,j:j+sx,2],results[0,:,:,2])
        
        
        outIM = outIM[0:-pdy, 0:-pdx,:]
        #predIM = (np.argmax(outIM, axis=2)) + 1
        predIM = outIM[:,:, 2]
        tmpImg = outIM[:,:, 1]
        predIM[predIM>0.05] = 3
        predIM[tmpImg > 0.3] = 2
        predIM[predIM<2] = 1
        outIM = None
        tmpImg = None
        
        return predIM
        
#%%        
    def predict_pixel_level(self, img, DLFeats, imageType):
        """Given image, applies the model onto the image
        """
        #YK 21119: calculate features for the first channels
        if imageType=='Neurites':
            feats = self.getFeats_Neurites(img[0], self.wSize, self.verbose)
        elif imageType=='Brightfield':
            feats = self.getFeats_Brightfield(img[0], self.wSize, self.verbose)
        else:
            feats = self.getFeats_Generic(img[0], self.wSize, self.verbose)

        if DLFeats > 0:
            feats2 = self.Extract_DL_Features_TF(img[0], DLFeats)
            feats = np.concatenate([feats,feats2],2)

        # YK 21119: then for the rest of the channels
        for i in range(1, len(img)):
            if imageType=='Neurites':
                feats2 = self.getFeats_Neurites(img[i], self.wSize, self.verbose)
            elif imageType=='Brightfield':
                feats2 = self.getFeats_Brightfield(img[i], self.wSize, self.verbose)
            else:
                feats2 = self.getFeats_Generic(img[i], self.wSize, self.verbose)
            
            feats = np.concatenate([feats,feats2],2)
            
            if DLFeats > 0:
                feats2 = self.Extract_DL_Features_TF(img[i], DLFeats)
                feats = np.concatenate([feats,feats2],2)
            
        if self.verbose:
            print('Shape of predict features: ', feats.shape)
        X = feats.reshape((img[0].shape[0]*img[0].shape[1],feats.shape[2]))
        predImg = self.model.predict(X)
        predImg = predImg.reshape(img[0].shape)        

        if self.MeanFeats is None:
            self.MeanFeats = []
        self.MeanFeats.append(np.mean(X,0)) 
            
        return predImg

    def postProcessing(self, img, kSize = 3):
        """Simple postProcessing: opening to clean the prediction maps
        """
        kernel = np.ones((kSize,kSize))
        outImg = cv2.morphologyEx(img, cv2.MORPH_CLOSE, kernel)
        outImg = cv2.morphologyEx(outImg, cv2.MORPH_OPEN, kernel)
    
        return outImg

