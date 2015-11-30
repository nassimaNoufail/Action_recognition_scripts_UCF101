import sys, os
import cv2
sys.path.append("../../caffe-dev/python/")
import caffe
import numpy as np
from scipy import stats

batch_size = 20

caffe.set_mode_gpu()
caffe.set_device(0)
net = caffe.Net("deploy.prototxt", "video__iter_10000.caffemodel", caffe.TEST)#"../model/Motion_iter_1000.caffemodel", caffe.TEST)
net.blobs['data'].reshape(batch_size, 20, 224, 224)

transformer = caffe.io.Transformer({'data': net.blobs['data'].data.shape})
transformer.set_transpose('data',(2, 0, 1))
transformer.set_mean('data', np.tile(128, 20))
transformer.set_raw_scale('data', 255)

res_fd = open('mot_res.txt','w')

image_batch = np.zeros((batch_size, 20, 224, 224))
image_name = []
count = 0
correct1 = 0
correct5 = 0
with open('test_motion_list.txt') as fd:
	sum_lines = len(fd.readlines())

with open('test_motion_list.txt') as fd:
	for line in fd:
		tokens = line.strip().split(' ')
		
		frames = [fr for fr in os.listdir(os.path.join(tokens[0], 'x')) if fr.endswith(".jpg")]
		frames_num = len(frames)
		randInd = np.random.randint(frames_num-10, size=batch_size)
		for j in range(batch_size):
			clip_buff = np.zeros((20, 224, 224))
			for i, frame in enumerate(frames[randInd[j]:randInd[j]+10]):
				im_x = caffe.io.load_image(os.path.join(tokens[0], 'x', frame))
				im_y = caffe.io.load_image(os.path.join(tokens[0], 'y', frame))
				#crop in the middle
				clip_buff[2*i, :, :] = im_x[16:-16,16:-16,0]
				clip_buff[2*i+1, :, :] = im_y[16:-16,16:-16,0]

			clip_buff = clip_buff.transpose((1, 2, 0))
			image_batch[j , :, :, :] = transformer.preprocess('data', clip_buff)
		label = int(tokens[1]) 
		image_name = tokens[0]
		
		count += 1
		net.blobs['data'].data[...] = image_batch
		out = net.forward()
		ranks = out['prob'].argsort()[:, -1:-6:-1]
		final_rank = np.zeros(5)
		
		# find mode for each position
		# ranks = ranks.transpose((1, 0))
		final_rank = stats.mode(ranks)[0][0].astype(int)
		
		if label in final_rank:
			correct5 += 1
		if label == final_rank[0]:
			correct1 += 1
		print os.path.basename(image_name) + " in " + "{:.3%}".format((0.0 + count)/sum_lines)
		print " Predicted class is "+' '.join(str(ele) for ele in final_rank)+" and ground truth is "+str(label)
		print " first one accuracy: " + str((0.0 + correct1)/count) + " first five accuracy: " + str((0.0 + correct5)/count)
		image_batch.fill(0)
		image_name = []
'''
remain = count % batch_size;
if remain != 0:
	net.blobs['data'].data[...] = image_batch
	out = net.forward()
	ranks = out['prob'].argsort()[:remain, -1:-6:-1]
	for im_nm, label, rank in zip(image_name, GT_labels[:remain], ranks):
				res_fd.write(im_nm+' '+str(label)+' '+' '.join(str(ele) for ele in rank)+'\n')
				if label in rank:
					correct5 += 1
				if label == rank[0]:
					correct1 += 1
				print os.path.basename(im_nm) + " in " + "{:.3%}".format((0.0 + count)/sum_lines)
				print " Predicted class is "+' '.join(str(ele) for ele in rank)+" and ground truth is "+str(label)
				print " first one accuracy: " + str((0.0 + correct1)/count) + " first five accuracy: " + str((0.0 + correct5)/count)
'''
res_fd.write("first one accuracy: " + str((0.0 + correct1)/count) + '\n')
res_fd.write("first five accuracy: " + str((0.0 + correct5)/count) + '\n')

res_fd.close()
