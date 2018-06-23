import torch
from torch import nn
from torch.nn import functional as F
import utils
import numpy as np


class LossBinary:
    """
    Loss defined as BCE - log(soft_jaccard)

    Vladimir Iglovikov, Sergey Mushinskiy, Vladimir Osin,
    Satellite Imagery Feature Detection using Deep Convolutional Neural Network: A Kaggle Competition
    arXiv:1706.06169
    """

    def __init__(self, jaccard_weight=0):
        self.nll_loss = nn.BCEWithLogitsLoss()
        self.jaccard_weight = jaccard_weight

    def __call__(self, outputs, targets):
        loss = self.nll_loss(outputs, targets)

        if self.jaccard_weight:
            eps = 1e-15
            jaccard_target = (targets == 1).float()
            jaccard_output = F.sigmoid(outputs)

            intersection = (jaccard_output * jaccard_target).sum()
            union = jaccard_output.sum() + jaccard_target.sum()

            loss -= self.jaccard_weight * torch.log((intersection + eps) / (union - intersection + eps))
        return loss


class LossMulti:
    def __init__(self, jaccard_weight=0, class_weights=None, num_classes=1):
        if class_weights is not None:
            nll_weight = utils.cuda(
                torch.from_numpy(class_weights.astype(np.float32)))
        else:
            nll_weight = None
        self.nll_loss = nn.NLLLoss2d(weight=nll_weight)
        self.jaccard_weight = jaccard_weight
        self.num_classes=num_classes

    def __call__(self, outputs, targets):
        loss = (1 - self.jaccard_weight) * self.nll_loss(outputs, targets)
        
        if self.jaccard_weight:            
            eps = 1e-15
            for cls in range(self.num_classes):
                jaccard_target = (targets == cls).float()
                jaccard_output = outputs[:, cls].exp()
                intersection = (jaccard_output * jaccard_target).sum()

                union = jaccard_output.sum() + jaccard_target.sum()
                loss += (1 - (intersection + eps) / (union - intersection + eps)) * self.jaccard_weight

        return loss

class LossBCE_DICE:
    """
    Loss defined as BCE + DICE
    """

    def __init__(self):
        self.nll_loss = nn.BCELoss()

    def __call__(self, outputs, targets):
        outputs = F.sigmoid(outputs)
        bce_loss = self.nll_loss(outputs, targets)
        dice_loss = (2. * (outputs * targets).sum() + 1) / (outputs.sum() + targets.sum() + 1)
        loss = bce_loss + (1 - dice_loss)
        return loss
