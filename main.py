import torch
from torchvision import datasets
from torchvision.transforms import ToTensor
from torch.utils.data import DataLoader
import torch.nn as nn
import torch.optim as optim
from models.vit import ViT
from models.cnn import CNN
from tqdm import tqdm
from dataset import KadidDataset
import torch.nn.functional as F
from skimage import io
from utils import rgb_to_grayscale
from models.trcnn import TrCNN

device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')


train_data = KadidDataset(
  csv_file="data/kadid10k/dmos.csv",
  root_dir="data/kadid10k/images",
  transform=ToTensor()
)

train_loader = DataLoader(train_data, batch_size=100, shuffle=True, num_workers=1)
# test_loader = DataLoader(test_data, batch_size=100, shuffle=True, num_workers=1)

criterion = nn.MSELoss()

cnn = CNN(
  diffusion_x=100, 
  diffusion_y=100
).to(device)

vit = ViT(
  channel=1, 
  height=100, 
  width=100, 
  n_patches=10, 
  n_blocks=2, 
  hidden_d=8, 
  n_heads=2, 
  out_d=1
).to(device)

cnn.load_state_dict(torch.load("cnn.pth"))
vit.load_state_dict(torch.load("vit.pth"))

trcnn = TrCNN(cnn, vit).to(device)

cnn_optimizer = optim.Adam(cnn.parameters(), lr=0.01)
vit_optimizer = optim.Adam(vit.parameters(), lr=0.01)

if __name__ == '__main__':
    
  for batch in tqdm(train_loader, desc='Training'):
    x, y = batch

    x = rgb_to_grayscale(x).unsqueeze(1) 
    y = y.reshape(-1, 1).float()
    x, y = x.to(device), y.to(device)
    y_hat = trcnn(x)
    loss = criterion(y_hat, y)
    cnn_optimizer.zero_grad()
    vit_optimizer.zero_grad()
    loss.backward()
    cnn_optimizer.step()
    vit_optimizer.step()

    print(f"Loss: {loss.item()}")

    break

  torch.save(vit.state_dict(), "vit.pth")
  torch.save(cnn.state_dict(), "cnn.pth")

  transform = ToTensor()  

  sample_image = io.imread("sample.png")
  sample_image = transform(sample_image)
  sample_image = sample_image.reshape(1, sample_image.shape[0], sample_image.shape[1], sample_image.shape[2])
  sample_image = rgb_to_grayscale(sample_image).unsqueeze(0)
  sample_image = sample_image.to(device)
  sample_output = cnn(sample_image)
  sample_output = vit(sample_output)
  print(sample_output)






  # with torch.no_grad():
  #   correct = 0
  #   total = 0

  #   for images, labels in tqdm(test_loader, desc='Testing'):

  #     images = images.to(device)
  #     labels = labels.to(device)

  #     test_output = cnn(images)
  #     test_output = vit(test_output)

  #     pred_y = torch.max(test_output, 1)[1].data.squeeze()
  #     total += labels.size(0)

  #     correct += (pred_y == labels).sum().item()

  #   accuracy = correct / total
  #   print(f"Test Accuracy of the model on the {total} test images: {accuracy}")