from abc import abstractmethod
import cv2
import logging

import eyeloop.config as config
from eyeloop.constants.processor_constants import *
from eyeloop.engine.models.circular import Circle
from eyeloop.engine.models.ellipsoid import Ellipse
from eyeloop.utilities.general_operations import to_int, tuple_int
from eyeloop.utilities.target_type import TargetType

logger = logging.getLogger(__name__)


# TODO(aelsen): min and max radii pulled out into constructor, should be in config

class Shape():
    def __init__(self, min_radius = 1, max_radius = 100):
        self.active = False
        self.type = None

        self.max_radius = max_radius
        self.min_radius = min_radius
        self.binarythreshold = -1
        self.blur = [3, 3]
        self.model = config.arguments.model
        self.threshold = len(CROP_STOCK) * self.min_radius * 1.05

        self.src = None
        self.src_dimms = (0, 0)
        self.center = -1
        self.fit_model = None


    # TODO(aelsen): pup_source DNE
    # def artefact(self, params):
    #     cv2.circle(config.engine.pup_source, tuple_int(params[0]), to_int(params[1] * self.expand), black, -1)

    # TODO(aelsen): not used
    # def clip(self, crop_list):
    #     np.clip(crop_list, self.min_radius, self.max_radius, out = crop_list)

    @abstractmethod
    def apply_threshold(self, src):
        raise NotImplementedError

    def cond(self, r):
        return r

    def distance(self, a, b):
        return np.sqrt((a[0] - b[0])**2 + (a[1] - b[1])**2)

    def fit(self, src, src_raw):
        try:
            r = self.walkout(src)
            # logger.info(f"Fitting processor {self.type} - r {r}")
            self.center = self.fit_model.fit(r)
            # logger.info(f"Fitting processor {self.type} - center {self.center}")
            # params = self.fit_model.params
            # self.artefact(params)

            return self.fit_model.params

        except IndexError as e:
            logger.warn(f"Failed to fit with processor {self.type} - fit index error - {e}")
            self.on_fit_failure(src, src_raw)

        except Exception as e:
            logger.warn(f"Failed to fit with processor {self.type} - Failed to fit shape model: {e}")
            self.on_fit_failure(src, src_raw)

    @abstractmethod
    def on_fit_failure(self, src, src_raw):
        pass

    def set_center(self, center):
        self.center = center
        self.standard_corners = [(0, 0), self.src_dimms]
        self.corners = self.standard_corners.copy()
        self.active = True
        #self.tracker = cv2.TrackerMedianFlow_create()
    
    def set_dimensions(self, dimms):
        self.src_dimms = dimms
    
    def track(self, frame):
        if (not self.active):
            return

        src_raw = frame.copy()
        src = frame.copy()

        # Performs a simple binarization and applies a smoothing gaussian kernel.
        src = self.apply_threshold(src)

        self.src = src

        return self.fit(src, src_raw)


class Pupil(Shape):
    def __init__(self, min_radius = 2, max_radius = 100):
        super().__init__(min_radius, max_radius)
        self.type = TargetType.PUPIL

        if self.model == "circular":
            self.fit_model = Circle()
        else:
            self.fit_model = Ellipse()

    def center_adjust(self, src_raw):
        # adjust settings:
        circles = cv2.HoughCircles(src_raw, cv2.HOUGH_GRADIENT, 1, 10, param1=200, param2=100, minRadius=self.min_radius, maxRadius=self.max_radius)

        if circles is None:
            return
        else:
            smallest = -1
            current = -1

            for circle in circles[0, :]:
                score = self.distance(circle[:2], self.center) + np.mean(src_raw[int(circle[1])-self.min_radius:int(circle[1])+self.min_radius, int(circle[0]-self.min_radius):int(circle[0]+self.min_radius)])

                src_raw[int(circle[1]), int(circle[0])] = 100
                cv2.imshow("kk", src_raw)
                cv2.waitKey(0)
                if smallest == -1:
                    smallest = score
                    current = circle[:2]
                elif score < smallest:
                    smallest = score
                    current = circle[:2]
                #self.center = circles[0,0][:1]
            self.center = tuple(current)

    def cond(self, r):
        # dists =  np.linalg.norm(np.mean([rx,ry],axis=1, dtype=np.float64)[:,np.newaxis] - np.array([rx, ry], dtype = np.float64), axis = 0)
        dists =  np.linalg.norm(np.mean(r,  axis = 0,dtype=np.float64) - r, axis = 1)

        mean = np.mean(dists)
        std = np.std(dists)
        lower, upper = mean - std, mean + std * .8
        cond_ = np.logical_and(np.greater_equal(dists, lower), np.less(dists, upper))
        return r[cond_]

    def apply_threshold(self, src):
        src = cv2.threshold(cv2.GaussianBlur(cv2.erode(src, kernel, iterations = 1), self.blur, 0), self.binarythreshold, 255, cv2.THRESH_BINARY_INV)[1]
        return src

    def on_fit_failure(self, src, src_raw):
        self.center_adjust(src_raw)

    def walkout(self, src):
        # diag_matrix = main_diagonal[:canvas_.shape[0], :canvas_.shape[1]]

        try:
            center = np.round(self.center).astype(int)
        except:
            logger.warn(f"Failed to perform walkout - failed to round center {self.center}")
            return


        canvas = np.array(src, dtype=int)#.copy()
        canvas[-1,:] = canvas[:,-1] = canvas[0,:] = canvas[:,0] = 0


        r = rr_2d.copy()

        crop_list = CROP_STOCK.copy()


        canvas_ = canvas[center[1]:, center[0]:]
        canv_shape0, canv_shape1 = canvas_.shape
        crop_canvas = np.flip(canvas[:center[1], :center[0]])
        crop_canv_shape0, crop_canv_shape1 = crop_canvas.shape

        crop_canvas2 = np.fliplr(canvas[center[1]:, :center[0]])
        crop_canv2_shape0, crop_canv2_shape1 = crop_canvas2.shape

        crop_canvas3 = np.flipud(canvas[:center[1], center[0]:])###
        crop_canv3_shape0, crop_canv3_shape1 = crop_canvas3.shape

        canvas2 = np.flip(canvas) # flip once


        crop_list=np.array([
        np.argmax(canvas_[:, 0][self.min_radius:self.max_radius] == 0), np.argmax(canvas_[0, :][self.min_radius:self.max_radius] == 0), np.argmax(canvas_[main_diagonal[:canv_shape0, :canv_shape1]][self.min_radius:self.max_radius] == 0),
        np.argmax(crop_canvas[main_diagonal[:crop_canv_shape0, :crop_canv_shape1]][self.min_radius:self.max_radius] == 0), np.argmax(crop_canvas2[main_diagonal[:crop_canv2_shape0, :crop_canv2_shape1]][self.min_radius:self.max_radius] == 0),
        np.argmax(crop_canvas3[main_diagonal[:crop_canv3_shape0, :crop_canv3_shape1]][self.min_radius:self.max_radius] == 0), np.argmax(canvas2[-center[1], -center[0]:][self.min_radius:self.max_radius] == 0), np.argmax(canvas2[-center[1]:, -center[0]][self.min_radius:self.max_radius] == 0),
        np.argmax(canvas_[ half_diagonal[:canv_shape0, :canv_shape1]][self.min_radius:self.max_radius] == 0), np.argmax(crop_canvas[half_diagonal[:crop_canv_shape0, :crop_canv_shape1]][self.min_radius:self.max_radius] == 0), np.argmax(crop_canvas2[half_diagonal[:crop_canv2_shape0, :crop_canv2_shape1]][self.min_radius:self.max_radius] == 0),
        np.argmax(crop_canvas3[half_diagonal[:crop_canv3_shape0, :crop_canv3_shape1]][self.min_radius:self.max_radius] == 0), np.argmax(canvas_[invhalf_diagonal[:canv_shape0, :canv_shape1]][self.min_radius:self.max_radius] == 0),
        np.argmax(crop_canvas[invhalf_diagonal[:crop_canv_shape0, :crop_canv_shape1]][self.min_radius:self.max_radius] == 0), np.argmax(crop_canvas2[invhalf_diagonal[:crop_canv2_shape0, :crop_canv2_shape1]][self.min_radius:self.max_radius] == 0),
        np.argmax(crop_canvas3[invhalf_diagonal[:crop_canv3_shape0, :crop_canv3_shape1]][self.min_radius:self.max_radius] == 0), np.argmax(canvas_[fourth_diagonal[:canv_shape0, :canv_shape1]][self.min_radius:self.max_radius] == 0), np.argmax(crop_canvas3[fourth_diagonal[:crop_canv3_shape0, :crop_canv3_shape1]][self.min_radius:self.max_radius] == 0),
        np.argmax(crop_canvas[fourth_diagonal[:crop_canv_shape0, :crop_canv_shape1]][self.min_radius:self.max_radius] == 0), np.argmax(crop_canvas2[fourth_diagonal[:crop_canv2_shape0, :crop_canv2_shape1]][self.min_radius:self.max_radius] == 0), np.argmax(canvas_[invfourth_diagonal[:canv_shape0, :canv_shape1]][self.min_radius:self.max_radius] == 0),
        np.argmax(crop_canvas2[invfourth_diagonal[:crop_canv2_shape0, :crop_canv2_shape1]][self.min_radius:self.max_radius] == 0), np.argmax(crop_canvas[invfourth_diagonal[:crop_canv_shape0, :crop_canv_shape1]][self.min_radius:self.max_radius] == 0), np.argmax(crop_canvas3[invfourth_diagonal[:crop_canv3_shape0, :crop_canv3_shape1]][self.min_radius:self.max_radius] == 0),
        np.argmax(canvas_[third_diagonal[:canv_shape0, :canv_shape1]][self.min_radius:self.max_radius] == 0), np.argmax(crop_canvas2[third_diagonal[:crop_canv2_shape0, :crop_canv2_shape1]][self.min_radius:self.max_radius] == 0), np.argmax(crop_canvas[third_diagonal[:crop_canv_shape0, :crop_canv_shape1]][self.min_radius:self.max_radius] == 0),
        np.argmax(crop_canvas3[third_diagonal[:crop_canv3_shape0, :crop_canv3_shape1]][self.min_radius:self.max_radius] == 0), np.argmax(canvas_[invthird_diagonal[:canv_shape0, :canv_shape1]][self.min_radius:self.max_radius] == 0), np.argmax(crop_canvas2[invthird_diagonal[:crop_canv2_shape0, :crop_canv2_shape1]][self.min_radius:self.max_radius] == 0),
        np.argmax(crop_canvas[invthird_diagonal[:crop_canv_shape0, :crop_canv_shape1]][self.min_radius:self.max_radius] == 0), np.argmax(crop_canvas3[invthird_diagonal[:crop_canv3_shape0, :crop_canv3_shape1]][self.min_radius:self.max_radius] == 0)
        ], dtype=int) + self.min_radius



        if np.sum(crop_list) < self.threshold:
            #origin inside corneal reflection?
            offset_list = np.array([
            np.argmax(canvas_[:, 0][1:] == 255), np.argmax(canvas_[0, :][1:] == 255), np.argmax(canvas_[main_diagonal[:canv_shape0, :canv_shape1]][1:] == 255),
            np.argmax(crop_canvas[main_diagonal[:crop_canv_shape0, :crop_canv_shape1]][1:] == 255), np.argmax(crop_canvas2[main_diagonal[:crop_canv2_shape0, :crop_canv2_shape1]][1:] == 255),
            np.argmax(crop_canvas3[main_diagonal[:crop_canv3_shape0, :crop_canv3_shape1]][1:] == 255), np.argmax(canvas2[-center[1], -center[0]:][1:] == 255), np.argmax(canvas2[-center[1]:, -center[0]][1:] == 255),
            np.argmax(canvas_[ half_diagonal[:canv_shape0, :canv_shape1]][1:] == 255), np.argmax(crop_canvas[half_diagonal[:crop_canv_shape0, :crop_canv_shape1]][1:] == 255), np.argmax(crop_canvas2[half_diagonal[:crop_canv2_shape0, :crop_canv2_shape1]][1:] == 255),
            np.argmax(crop_canvas3[half_diagonal[:crop_canv3_shape0, :crop_canv3_shape1]][1:] == 255), np.argmax(canvas_[invhalf_diagonal[:canv_shape0, :canv_shape1]][1:] == 255),
            np.argmax(crop_canvas[invhalf_diagonal[:crop_canv_shape0, :crop_canv_shape1]][1:] == 255), np.argmax(crop_canvas2[invhalf_diagonal[:crop_canv2_shape0, :crop_canv2_shape1]][1:] == 255),
            np.argmax(crop_canvas3[invhalf_diagonal[:crop_canv3_shape0, :crop_canv3_shape1]][1:] == 255), np.argmax(canvas_[fourth_diagonal[:canv_shape0, :canv_shape1]][1:] == 255), np.argmax(crop_canvas3[fourth_diagonal[:crop_canv3_shape0, :crop_canv3_shape1]][1:] == 255),
            np.argmax(crop_canvas[fourth_diagonal[:crop_canv_shape0, :crop_canv_shape1]][1:] == 255), np.argmax(crop_canvas2[fourth_diagonal[:crop_canv2_shape0, :crop_canv2_shape1]][1:] == 255), np.argmax(canvas_[invfourth_diagonal[:canv_shape0, :canv_shape1]][1:] == 255),
            np.argmax(crop_canvas2[invfourth_diagonal[:crop_canv2_shape0, :crop_canv2_shape1]][1:] == 255), np.argmax(crop_canvas[invfourth_diagonal[:crop_canv_shape0, :crop_canv_shape1]][1:] == 255), np.argmax(crop_canvas3[invfourth_diagonal[:crop_canv3_shape0, :crop_canv3_shape1]][1:] == 255),
            np.argmax(canvas_[third_diagonal[:canv_shape0, :canv_shape1]][1:] == 255), np.argmax(crop_canvas2[third_diagonal[:crop_canv2_shape0, :crop_canv2_shape1]][1:] == 255), np.argmax(crop_canvas[third_diagonal[:crop_canv_shape0, :crop_canv_shape1]][1:] == 255),
            np.argmax(crop_canvas3[third_diagonal[:crop_canv3_shape0, :crop_canv3_shape1]][1:] == 255), np.argmax(canvas_[invthird_diagonal[:canv_shape0, :canv_shape1]][1:] == 255), np.argmax(crop_canvas2[invthird_diagonal[:crop_canv2_shape0, :crop_canv2_shape1]][1:] == 255),
            np.argmax(crop_canvas[invthird_diagonal[:crop_canv_shape0, :crop_canv_shape1]][1:] == 255), np.argmax(crop_canvas3[invthird_diagonal[:crop_canv3_shape0, :crop_canv3_shape1]][1:] == 255)
            ], dtype=int) + 1


            crop_list=np.array([
            np.argmax(canvas_[:, 0][offset_list[0]:] == 0), np.argmax(canvas_[0, :][offset_list[1]:] == 0), np.argmax(canvas_[main_diagonal[:canv_shape0, :canv_shape1]][offset_list[2]:] == 0),
            np.argmax(crop_canvas[main_diagonal[:crop_canv_shape0, :crop_canv_shape1]][offset_list[3]:] == 0), np.argmax(crop_canvas2[main_diagonal[:crop_canv2_shape0, :crop_canv2_shape1]][offset_list[4]:] == 0),
            np.argmax(crop_canvas3[main_diagonal[:crop_canv3_shape0, :crop_canv3_shape1]][offset_list[5]:] == 0), np.argmax(canvas2[-center[1], -center[0]:][offset_list[6]:] == 0), np.argmax(canvas2[-center[1]:, -center[0]][offset_list[7]:] == 0),
            np.argmax(canvas_[ half_diagonal[:canv_shape0, :canv_shape1]][offset_list[8]:] == 0), np.argmax(crop_canvas[half_diagonal[:crop_canv_shape0, :crop_canv_shape1]][offset_list[9]:] == 0), np.argmax(crop_canvas2[half_diagonal[:crop_canv2_shape0, :crop_canv2_shape1]][offset_list[10]:] == 0),
            np.argmax(crop_canvas3[half_diagonal[:crop_canv3_shape0, :crop_canv3_shape1]][offset_list[11]:] == 0), np.argmax(canvas_[invhalf_diagonal[:canv_shape0, :canv_shape1]][offset_list[12]:] == 0),
            np.argmax(crop_canvas[invhalf_diagonal[:crop_canv_shape0, :crop_canv_shape1]][offset_list[13]:] == 0), np.argmax(crop_canvas2[invhalf_diagonal[:crop_canv2_shape0, :crop_canv2_shape1]][offset_list[14]:] == 0),
            np.argmax(crop_canvas3[invhalf_diagonal[:crop_canv3_shape0, :crop_canv3_shape1]][offset_list[15]:] == 0), np.argmax(canvas_[fourth_diagonal[:canv_shape0, :canv_shape1]][offset_list[16]:] == 0), np.argmax(crop_canvas3[fourth_diagonal[:crop_canv3_shape0, :crop_canv3_shape1]][offset_list[17]:] == 0),
            np.argmax(crop_canvas[fourth_diagonal[:crop_canv_shape0, :crop_canv_shape1]][offset_list[18]:] == 0), np.argmax(crop_canvas2[fourth_diagonal[:crop_canv2_shape0, :crop_canv2_shape1]][offset_list[19]:] == 0), np.argmax(canvas_[invfourth_diagonal[:canv_shape0, :canv_shape1]][offset_list[20]:] == 0),
            np.argmax(crop_canvas2[invfourth_diagonal[:crop_canv2_shape0, :crop_canv2_shape1]][offset_list[21]:] == 0), np.argmax(crop_canvas[invfourth_diagonal[:crop_canv_shape0, :crop_canv_shape1]][offset_list[22]:] == 0), np.argmax(crop_canvas3[invfourth_diagonal[:crop_canv3_shape0, :crop_canv3_shape1]][offset_list[23]:] == 0),
            np.argmax(canvas_[third_diagonal[:canv_shape0, :canv_shape1]][offset_list[24]:] == 0), np.argmax(crop_canvas2[third_diagonal[:crop_canv2_shape0, :crop_canv2_shape1]][offset_list[25]:] == 0), np.argmax(crop_canvas[third_diagonal[:crop_canv_shape0, :crop_canv_shape1]][offset_list[26]:] == 0),
            np.argmax(crop_canvas3[third_diagonal[:crop_canv3_shape0, :crop_canv3_shape1]][offset_list[27]:] == 0), np.argmax(canvas_[invthird_diagonal[:canv_shape0, :canv_shape1]][offset_list[28]:] == 0), np.argmax(crop_canvas2[invthird_diagonal[:crop_canv2_shape0, :crop_canv2_shape1]][offset_list[29]:] == 0),
            np.argmax(crop_canvas[invthird_diagonal[:crop_canv_shape0, :crop_canv_shape1]][offset_list[30]:] == 0), np.argmax(crop_canvas3[invthird_diagonal[:crop_canv3_shape0, :crop_canv3_shape1]][offset_list[31]:] == 0)
            ], dtype=int) + offset_list


            if np.sum(crop_list) < self.threshold:
                raise IndexError("Lost track, do reset")

        r[:8,:] = center
        r[ry_add, 1] += crop_list[ry_add]
        r[rx_add, 0] += crop_list[rx_add]
        r[ry_subtract, 1] -= crop_list[ry_subtract] #
        r[rx_subtract, 0] -= crop_list[rx_subtract]
        r[rx_multiplied, 0] *= rx_multiply
        r[ry_multiplied, 1] *= ry_multiply
        r[8:,:] += center


            #return
        # try:
        #    canvas_rgb = cv2.cvtColor(src, cv2.COLOR_GRAY2RGB)
        #    cy, cx = np.mean(ry, dtype=int), np.mean(rx, dtype=int)
        #    canvas_rgb[cy,cx] = [0,0,255]
        #    canvas_rgb[ry.astype("int"), rx.astype("int")] = [0,0,255]
        #    canvas_rgb[center[1], center[0]] = [255,0,0]
        #    rx1,ry1 = self.cond(rx, ry, crop_list)
        #    canvas_rgb[ry1.astype("int"), rx1.astype("int")] = [0,255,0]
        #    cv2.imshow("JJJ", canvas_rgb)
        #    cv2.waitKey(5)
        # except Exception as e:
        #    logger.info(e)

        # return self.cond(r, crop_list)#rx[cond_], ry[cond_]#rx, ry
        return self.cond(r)



class CornealReflection(Shape):
    def __init__(self, n = 0, min_radius = 1, max_radius = 20):
        super().__init__(min_radius, max_radius)
        self.type = TargetType.CORNEAL_REFLECTION
        self.fit_model = Circle()
        # self.fit_model = Center() # old
        # self.expand = 1.2 # old

    def apply_threshold(self, src):
        _, src = cv2.threshold(cv2.GaussianBlur(src, self.blur, 0), self.binarythreshold, 255, cv2.THRESH_BINARY)
        return src

    def walkout(self, src):
        # diag_matrix = main_diagonal[:canvas_.shape[0], :canvas_.shape[1]]

        try:
            center = np.round(self.center).astype(int)
        except:
            logger.warn(f"Failed to perform walkout - failed to round center {self.center}")
            return

        #canvas = np.array(src, dtype=int)#.copy()

        r = rr_2d_cr.copy()

        crop_list = CROP_STOCK_CR.copy()
        #rx = np.zeros(4)
        #ry = np.zeros(4)

        canvas_ = src[center[1]:, center[0]:]

        crop_list[0] = np.argmax(canvas_[:, 0] == 0) #- 1
        #crop_ = np.argmax(canvas_[:, 0] == 0) #- 1

        #ry[0], rx[0] = crop_ + center[1], center[0]


        crop_list[2] = np.argmax(canvas_[0, :] == 0) #- 1
        #crop_ = np.argmax(canvas_[0, :] == 0) #- 1

    #    ry[2], rx[2] = center[1], crop_ + center[0]


        canvas = np.flip(src) # flip once

        crop_list[3] = -np.argmax(canvas[-center[1], -center[0]:] == 0)
        #crop_ = np.argmax(canvas[-center[1], -center[0]:] == 0)# - 1

        #ry[3], rx[3] = center[1], -crop_ + center[0]


        crop_list[1]= -np.argmax(canvas[-center[1]:, -center[0]] == 0)
    #    crop_ = np.argmax(canvas[-center[1]:, -center[0]] == 0)

        #ry[1], rx[1] = -crop_ + center[1], center[0]
        #logger.info()

        #logger.info(r, crop_list)
        r[:,:] = center

        r[:2, 1] += crop_list[:2]
        r[2:, 0] += crop_list[2:]



        #logger.info(r, rx, ry)

        # try:
        #
        #    canvas_rgb = cv2.cvtColor(src, cv2.COLOR_GRAY2RGB)
        #
        #   # canvas_rgb[cy,cx] = [0,0,255]
        #    #canvas_rgb[ry.astype("int"), rx.astype("int")] = [0,255,0]
        #    canvas_rgb[r[:,1].astype("int"), r[:,0].astype("int")] = [0,0,255]
        #    #canvas_rgb[center[1], center[0]] = [255,0,0]
        #    #rx1,ry1 = self.cond(rx, ry, crop_list)
        #   # canvas_rgb[ry1.astype("int"), rx1.astype("int")] = [0,255,0]
        #    cv2.imshow("JJJ", canvas_rgb)
        #    cv2.waitKey(5)
        # except Exception as e:
        #    logger.info(e)


        return r#rx[cond_], ry[cond_]#rx, ry