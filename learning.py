import torch.optim as optim
from torch.autograd import Variable
import torch.nn as nn
import params
import utils
import torch
from loss import margin_loss
import test
import visdom
import numpy as np
import datetime
from torch.optim import lr_scheduler


def learning_process(train_loader, network, criterion, test_loader, mode):
    vis = visdom.Visdom()
    optimizer = optim.SGD(network.parameters(),
                          lr=params.learning_rate,
                          momentum=params.momentum)

    # Decay LR by a factor of 0.1 every 7 epochs
    exp_lr_scheduler = lr_scheduler.StepLR(optimizer,
                                           step_size=params.learning_rate_decay_epoch,
                                           gamma=params.learning_rate_decay_coefficient)

    for epoch in range(params.number_of_epochs):  # loop over the dataset multiple times
        exp_lr_scheduler.step(epoch=epoch)
        print('current_learning_rate =' , optimizer.param_groups[0]['lr'])
        print(datetime.datetime.now())
        running_loss = 0.0
        for i, data in enumerate(train_loader, 0):
            # get the inputs
            # inputs are [torch.FloatTensor of size 4x3x32x32]
            # labels are [torch.LongTensor of size 4]
            # here 4 is a batch size and 3 is a number of channels in the input images
            # 32x32 is a size of input image
            inputs, labels = data

            # wrap them in Variable
            inputs, labels = Variable(inputs.cuda()), Variable(labels.cuda())

            # zero the parameter gradients
            optimizer.zero_grad()

            # forward + backward + optimize
            outputs = network(inputs)

            # representation = network.get_representation(inputs)

            loss = criterion(outputs, labels)
            loss.backward()
            optimizer.step()

            # print statistics
            running_loss += loss.data[0]
            if i % params.skip_step == 0:  # print every 2000 mini-batches
                print('[ephoch %d, itteration in the epoch %5d] loss: %.10f' %
                      (epoch + 1, i + 1, running_loss / params.skip_step))
                r_loss = running_loss / params.skip_step
                #vis.line(Y=np.array([r_loss]), X=np.array([epoch]),
                #         update='append', win='loss')

                running_loss = 0.0
                # print the train accuracy at every epoch
                # to see if it is enough to start representation training
                # or we should proceed with classification
                if mode == params.mode_classification:
                    accuracy = test.test(test_loader=test_loader, network=network)
                    #vis.line(Y=accuracy, X=epoch, update='append', win='accuracy')

        if epoch % 1 == 0:
            utils.save_checkpoint(network=network,
                                  optimizer=optimizer,
                                  filename=params.name_prefix_for_saved_model + '-%d' % epoch,
                                  epoch=epoch)


    print('Finished Training')
