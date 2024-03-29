import torch.nn as nn
import torch
from torch.utils.data import DataLoader
from torch.utils.tensorboard import SummaryWriter


class Trainer(nn.Module):
    def __init__(self, model, loss_fn, optimizer,lr, epochs: int, train_dataloader: DataLoader, val_dataloader: DataLoader, \
                 device: str = "cpu", writer: SummaryWriter = None):
        super(Trainer, self).__init__()
        self.model = model
        self.loss_fn = loss_fn
        self.optimizer = optimizer
        self.epochs = epochs
        self.train_dataloader = train_dataloader
        self.val_dataloader = val_dataloader
        self.device = device
        self.writer = writer
        self.lr=lr

    def _step_train(self):
        train_loss, train_correct = 0.0, 0.0
        num_batches = len(self.train_dataloader)
        size = len(self.train_dataloader.dataset)
        # Sets model to train mode
        self.model.train()
        for _, (X, y) in enumerate(self.train_dataloader):
            X = X.to(self.device)
            frame_size = X.shape[1]

            y = y.type(torch.LongTensor).to(self.device)

            # Makes predictions
            pred = self.model(X)
            pred_target = pred.argmax(1)

            # Computes loss
            loss_arr = []
            for i in range(y.shape[1]):
                loss = self.loss_fn(pred, y[:,i])
                loss_arr.append(loss)
                train_correct += torch.sum(pred_target == y[:,i]).item()

            # Computes gradients
            self.optimizer.zero_grad()
            for i in range(y.shape[1]):
                loss_arr[i].backward(retain_graph=True)
                
            # Updates parameters and zeroes gradients
            self.optimizer.step()

            train_loss += sum(loss_arr) / len(loss_arr)

        train_loss /= num_batches
        train_correct /= (size * frame_size)

        return train_loss, train_correct

    def _step_val(self):

        size = len(self.val_dataloader.dataset)
        num_batches = len(self.val_dataloader)
        self.model.eval()
        val_loss, val_correct = 0, 0
        with torch.no_grad():
            for _, (X, y) in enumerate(self.val_dataloader):
                X = X.to(self.device)
                frame_size = X.shape[1]

                y = y.type(torch.LongTensor).to(self.device)

                pred = self.model(X)

                val_loss_arr = []

                for i in range(y.shape[1]):
                    loss = self.loss_fn(pred, y[:,i])
                    val_loss_arr.append(loss)
                    val_correct += (pred.argmax(dim=1) == y[:,i]).sum().item()

                val_loss += sum(val_loss_arr) / len(val_loss_arr)

        val_loss /= num_batches
        val_correct /= (size * frame_size)

        return val_loss, val_correct

    def train(self):
        for t in range(self.epochs):
            print(f"Epoch {t}/{self.epochs}", end="\r")
            train_loss, train_correct = self._step_train()
            val_loss, val_correct = self._step_val()
            #Tensorboard
            self.writer.add_scalar('train_loss', train_loss, t)
            self.writer.add_scalar('val_loss', val_loss, t)
            self.writer.add_scalar('train_acc', train_correct, t)
            self.writer.add_scalar('val_acc', val_correct, t)
            self.lr.step(train_loss)
        print()
