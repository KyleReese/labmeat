from VasGen2 import VasGen2
from equations import *
import os
import math
import matplotlib

if os.sys.platform == "linux" or os.sys.platform == "linux2":
    matplotlib.use('TKAgg')
elif os.sys.platform == "darwin":
    matplotlib.use('MacOSX')
import matplotlib.pyplot as plt

import random
import time

import imageio
from natsort import natsorted, ns

import autograd.numpy as np
from autograd import grad
from autograd.scipy.integrate import odeint
from autograd.builtins import tuple
from autograd.misc.optimizers import adam
import autograd.numpy.random as npr
import autograd.scipy.signal as sig
from timeit import default_timer as timer
from meatModel2d import getDynamics, getTrueParameters, getSampleParameters


def create_remove_imgs():
    path_to_diffuse_pngs = 'Hillclimb/diffusePngs/'
    sim_img_folder = 'Hillclimb/imgs/'
    sim_graph_folder = 'Hillclimb/graphs/'
    sim_fig_folder = 'Hillclimb/figs/'
    if not os.path.exists(path_to_diffuse_pngs):
        os.makedirs(path_to_diffuse_pngs)

    if not os.path.exists(sim_img_folder):
        os.makedirs(sim_img_folder)

    if not os.path.exists(sim_graph_folder):
        os.makedirs(sim_graph_folder)

    if not os.path.exists(sim_fig_folder):
        os.makedirs(sim_fig_folder)

    for img_file in os.listdir(path_to_diffuse_pngs):
        os.remove(path_to_diffuse_pngs + img_file)

    if os.path.exists(sim_img_folder):
        for img_file in os.listdir(sim_img_folder):
            os.remove(sim_img_folder + img_file)

    if os.path.exists(sim_graph_folder):
        for img_file in os.listdir(sim_graph_folder):
            os.remove(sim_graph_folder + img_file)

    if os.path.exists(sim_fig_folder):
        for img_file in os.listdir(sim_fig_folder):
            os.remove(sim_fig_folder + img_file)

def adjustMoveRate(num):
    num = num/1.5
    if num < 0.5:
        if num > 0:
            num = 0.5
        elif num > -0.5:
            num = -0.5
    return num

def saveImageOne(iteration):
    fig.savefig('HillClimb/figs/' + str(iteration) + '.png', size=[1600,400])

if __name__ == "__main__":
    print("Climbing the hill")
    numNodes = 1
    grid_size = 40
    path_to_diffuse_pngs = 'Hillclimb/diffusePngs/'
    sim_img_folder = 'Hillclimb/imgs/'
    sim_graph_folder = 'Hillclimb/graphs/'

    create_remove_imgs()

    vas_structure = VasGen2(max_range=grid_size, num_of_nodes=numNodes, side_nodes=False)
    vas_structure.print_images(graph_name='HillClimb/HillClimb_startGraph.png', img_name='HillClimb/HillClimb_startImg.png')

    test_movement = np.array([-5, -2, -1, 0, 1, 2, 5])

    flowDict = computeFlow(vas_structure)
    vas_structure.add_flows_to_img(flowDict)
    img = vas_structure.img
    diffused_img = img
    
    img = np.array(img)
    vas_structure.Q = img

    mvable_pts = vas_structure.moveable_pts
    
    all_loss = []
    time_lst = []

    # Set up figures
    fig = plt.figure(figsize=(16, 6), facecolor='white')
    fig.suptitle('Hill Climber', fontsize=16)
    ax_loss         = fig.add_subplot(231, frameon=True)
    ax_cpu          = fig.add_subplot(232, frameon=True)
    ax_node_graph   = fig.add_subplot(233, frameon=True)
    ax_nutrient     = fig.add_subplot(234, frameon=True)
    ax_product      = fig.add_subplot(235, frameon=True)
    ax_img          = fig.add_subplot(236, frameon=True)
    plt.show(block=False)

    def callback(mvable_pts, iter, nowLoss, time_duration):
        # ==== LOSS as a function of TIME ==== #
        ax_loss.cla()
        ax_loss.set_title('Optimization Gain')
        ax_loss.set_xlabel('Iteration')
        ax_loss.set_ylabel('Fitness')
        nowLoss = nowLoss
        all_loss.append(nowLoss)
        iteration = np.arange(0, len(all_loss), 1)

        ax_loss.plot(iteration, all_loss, '-', linestyle = 'solid', label='Gain') #, color = colors[i]
        ax_loss.set_xlim(iteration.min(), iteration.max())
        ax_loss.legend(loc = "upper left")

        # ==== CPU Time ==== #
        ax_cpu.cla()
        ax_cpu.set_title('CPU Time Per Iteration')
        ax_cpu.set_xlabel('Iteration')
        ax_cpu.set_ylabel('CPU Time (s)')
        time_lst.append(time_duration)
        ax_cpu.plot(iteration, time_lst, '-', linestyle = 'solid', label='CPU Time')
        ax_cpu.legend(loc = "upper left")

        # ==== Plots the Node Graph ==== #
        ax_node_graph.cla()
        ax_node_graph.set_title('Node Graph')
        for j, s in enumerate(vas_structure.tri.simplices):
            p = np.array(vas_structure.pts)[s].mean(axis=0)
            ax_node_graph.text(p[0], p[1], 'Cell #%d' % j, ha='center') # label triangles
        ax_node_graph.triplot(np.array(vas_structure.pts)[:,0], np.array(vas_structure.pts)[:,1], vas_structure.tri.simplices)
        ax_node_graph.plot(np.array(vas_structure.pts)[:,0], np.array(vas_structure.pts)[:,1], 'o')

        # ==== Plot Flow Img ==== #
        ax_img.cla()
        ax_img.set_title('Flow Image')
        ax_img.tick_params(axis='x', which='both', bottom=False, top=False, labelbottom=False)
        ax_img.tick_params(axis='y', which='both', left=False, right=False, labelleft=False)
        ax_img.imshow(np.rot90(np.array(vas_structure.img)[1:,1:]), cmap='jet')

        # ==== Plot Product Image ==== #
        ax_product.cla()
        ax_product.set_title('Product Image')
        ax_product.tick_params(axis='x', which='both', bottom=False, top=False, labelbottom=False)
        ax_product.tick_params(axis='y', which='both', left=False, right=False, labelleft=False)
        ax_product.imshow(np.rot90(np.array(vas_structure.product_values)), cmap='jet')
        
        # # ==== Plot Nutrient Image ==== #
        ax_nutrient.cla()
        ax_nutrient.set_title('Nutrient Image')
        ax_nutrient.tick_params(axis='x', which='both', bottom=False, top=False, labelbottom=False)
        ax_nutrient.tick_params(axis='y', which='both', left=False, right=False, labelleft=False)
        ax_nutrient.imshow(np.rot90(np.array(vas_structure.nutrient_values)), cmap='jet')

        plt.subplots_adjust( wspace = 0.5, hspace = 0.5 )
        plt.draw()
        saveImageOne(iter)
        plt.pause(0.001)
        return 3

    dImproved = False
    currentLoss = -1
    i = 0
    timesNotImproved = 0
    inc_index_x = 0.01
    inc_index_y = 0
    index = 0
    moveRate = 0.1
    while timesNotImproved < 5:
        start = time.time()

        if not dImproved:
            if timesNotImproved == 1:
                inc_index_x = moveRate
                inc_index_y = 0
            elif timesNotImproved == 2:
                inc_index_x = -1 * moveRate
                inc_index_y = 0
            elif timesNotImproved == 3:
                inc_index_x = 0
                inc_index_y = moveRate
            elif timesNotImproved == 4:
                inc_index_x = 0
                inc_index_y = -1 * moveRate
            # index = random.randrange(0, numNodes)
            # inc_index_x = np.random.choice(test_movement, 1, replace=False)[0]
            # inc_index_y = np.random.choice(test_movement, 1, replace=False)[0]
        else:
            # inc_index_x = adjustMoveRate(inc_index_x)
            # inc_index_y = adjustMoveRate(inc_index_y)
            timesNotImproved = 0

        originalPoints = vas_structure.moveable_pts[index]
            
        test_x = vas_structure.moveable_pts[index][0] + inc_index_x
        test_y = vas_structure.moveable_pts[index][1] + inc_index_y

        if test_x < 1:
            test_x = 1
        if test_x > grid_size-1:
            test_x = grid_size-1

        if test_y < 1:
            test_y = 1
        if test_y > grid_size-1:
            test_y = grid_size

        vas_structure.moveable_pts[index] = [test_x, test_y]
        mvable_pts = vas_structure.moveable_pts
        vas_structure.update_hillclimb_pts(mvable_pts)
        flowDict = computeFlow(vas_structure)
        vas_structure.add_flows_to_img(flowDict)
        
        
        (dynamicsTrue, fitnessList, odeDeltaList, pdeDeltaList, values) = getDynamics(vas_structure, 
                        getTrueParameters(), 
                        nonLinear = True, 
                        movablePts = vas_structure.moveable_pts,
                        runParameters = getSampleParameters())

        (max_t, count) = getSampleParameters()
        loss = vas_structure.nutrient_values[10][10]#np.cumsum(fitnessList[int(count*.30):-1])[-1]#fitness(mvable_pts, i)
        print('loss', loss)
        
        print('Point change:', originalPoints, mvable_pts[index])
        if loss > currentLoss:
            currentLoss = loss
            dImproved = True
            print(i, 'REDUCED LOSS:', loss)
            timesNotImproved = 0
        else:
            vas_structure.moveable_pts[index] = originalPoints
            mvable_pts = vas_structure.moveable_pts
            dImproved = False
            print(i, 'LOSS IS >= CURRENT', loss)
            timesNotImproved += 1

        end = time.time()
        elapsedTime = end-start
        callback(mvable_pts, i, currentLoss, elapsedTime)
        
        vas_structure.print_images(graph_name=sim_graph_folder+'test_graph'+str(i)+'.png', img_name=sim_img_folder+'test_img'+str(i)+'.png')
        i += 1
    print('final moveable points:', vas_structure.moveable_pts)


    def img_path_generator(path_to_img_dir):
        for i, file_name in enumerate(natsorted(os.listdir(path_to_img_dir), key=lambda y: y.lower())):
            if file_name.endswith('.png'):
                if not i == 0:
                    file_path = os.path.join(path_to_img_dir, file_name)
                    yield imageio.imread(file_path)

    sim_fig_folder = 'HillClimb/figs/'
    imageio.mimsave('HillClimb/HillClimb_Figs.gif', img_path_generator(sim_fig_folder), fps=10)
