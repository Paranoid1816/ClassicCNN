import  torch
from    torch.utils.data import DataLoader
from    torchvision import datasets
from    torchvision import transforms
from    torch import nn, optim

from    lenet5 import Lenet5
from resnet import ResNet18
from AlexNet import AlexNet
from VGG16 import VGG16
import visdom


def main():
    path = 'D://驾驶行为//imgs//train//'
    batch_size = 16
    viz = visdom.Visdom()
    test = datasets.ImageFolder(path, transform=transforms.Compose([
        transforms.Resize((224,224)),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406],
                                 std=[0.229, 0.224, 0.225])
    ]))
    train_size = int(0.8 * len(test))
    test_size = len(test) - train_size
    train_dataset, test_dataset = torch.utils.data.random_split(test, [train_size, test_size])
    cifar_train = DataLoader(train_dataset, shuffle=True, batch_size=batch_size,num_workers=8)
    cifar_test = DataLoader(test_dataset, shuffle=True, batch_size=batch_size,num_workers=8)
    print(len(test),len(train_dataset),len(test_dataset))


    device = torch.device('cuda')
    # model = Lenet5().to(device)
    model = ResNet18().to(device)
    mode11 = VGG16().to(device)

    criteon = nn.CrossEntropyLoss().to(device)
    criteon1 = nn.CrossEntropyLoss().to(device)

    optimizer = optim.Adam(model.parameters(), lr=0.00001,weight_decay=0.01)
    optimizer1 = optim.Adam(model.parameters(), lr=0.00001, weight_decay=0.01)

    print(model,mode11)
    best_acc,best_epoch = 0,0
    # model.load_state_dict(torch.load('best_checkpoint.model'))
    global_step = 0
    lr = 0.00001
    for epoch in range(20):
        if (epoch+1)%5 == 0:
            lr/=2
            optimizer = optim.Adam(model.parameters(), lr=lr,weight_decay=0.01)
            optimizer1 = optim.Adam(model.parameters(), lr=lr, weight_decay=0.01)
        model.train()
        mode11.train()
        for batchidx, (x, label) in enumerate(cifar_train):
            # [b, 3, 32, 32]
            # [b]
            x, label = x.to(device), label.to(device)


            logits = model(x)
            logits1 = mode11(x)

            # logits: [b, 10]
            # label:  [b]
            # loss: tensor scalar
            loss = criteon(logits, label)
            loss1 = criteon(logits1,label)

            # backprop
            optimizer.zero_grad()
            optimizer.zero_grad()
            loss.backward()
            loss1.backward()
            optimizer.step()
            optimizer1.step()
            viz.line([loss.item()], [global_step], win='loss', update='append')
            viz.line([loss1.item()], [global_step], win='loss1', update='append')
            global_step+=1

        print('epoch:',epoch, 'resnet loss:', loss.item(),'vgg loss:',loss1.item())

        model.eval()
        mode11.eval()
        with torch.no_grad():
            # test
            total_correct = 0
            total_num = 0
            for x, label in cifar_train:
                # [b, 3, 32, 32]
                # [b]
                x, label = x.to(device), label.to(device)

                # [b, 10]
                logits = model(x)
                logits1 = mode11(x)
                em_logits = 0.6*logits1+0.4*logits
                # [b]
                pred = em_logits.argmax(dim=1)
                # [b] vs [b] => scalar tensor
                correct = torch.eq(pred, label).float().sum().item()
                total_correct += correct
                total_num += x.size(0)
                # print(correct)

            acc = total_correct / total_num
        print("train acc :",acc)

        model.eval()
        mode11.eval()
        with torch.no_grad():
            # test
            total_correct = 0
            total_num = 0
            for x, label in cifar_test:
                # [b, 3, 32, 32]
                # [b]
                x, label = x.to(device), label.to(device)

                # [b, 10]
                logits = model(x)
                logits1 = mode11(x)
                em_logits = 0.6 * logits1 + 0.4 * logits
                # [b]
                pred = em_logits.argmax(dim=1)
                # [b] vs [b] => scalar tensor
                correct = torch.eq(pred, label).float().sum().item()
                total_correct += correct
                total_num += x.size(0)
                # print(correct)

            acc = total_correct / total_num
            if acc>best_acc:
                best_epoch = epoch
                best_acc = acc
                if epoch == 0:continue
                torch.save(model.state_dict(),'best_checkpoint_resnet18.model')
        print('epoch:',epoch, 'test acc:', acc)
        print('best epoch:',best_epoch,'best acc:',best_acc)


if __name__ == '__main__':
    main()
