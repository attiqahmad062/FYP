import { Product } from '../../types/product';
import ProductOne from '../../images/product/product-01.png';
import ProductTwo from '../../images/product/product-02.png';
import ProductThree from '../../images/product/product-03.png';
import ProductFour from '../../images/product/product-04.png';
const productData: Product[] = [
  {
    image: ProductOne,
    name: 'Apple Watch Series 7',
    category: 'Electronics',
    price: 296,
    sold: 22,
    profit: 45,
  },
  {
    image: ProductTwo,
    name: 'Macbook Pro M1',
    category: 'Electronics',
    price: 546,
    sold: 12,
    profit: 125,
  },
  {
    image: ProductThree,
    name: 'Dell Inspiron 15',
    category: 'Electronics',
    price: 443,
    sold: 64,
    profit: 247,
  },
  {
    image: ProductFour,
    name: 'HP Probook 450',
    category: 'Electronics',
    price: 499,
    sold: 72,
    profit: 103,
  },
];

const TableTwo = () => {
  return (
    <div className="bg-white border border-stroke rounded-sm shadow-default dark:bg-boxdark dark:border-strokedark">
      <div className="md:px-6 px-4 py-6 xl:px-7.5">
        <h4 className="text-black text-xl dark:text-white font-semibold">
          Top Products
        </h4>
      </div>

      <div className="grid grid-cols-6 border-stroke border-t 2xl:px-7.5 dark:border-strokedark md:px-6 px-4 py-4.5 sm:grid-cols-8">
        <div className="col-span-3 flex items-center">
          <p className="font-medium">Product Name</p>
        </div>
        <div className="col-span-2 hidden items-center sm:flex">
          <p className="font-medium">Category</p>
        </div>
        <div className="col-span-1 flex items-center">
          <p className="font-medium">Price</p>
        </div>
        <div className="col-span-1 flex items-center">
          <p className="font-medium">Sold</p>
        </div>
        <div className="col-span-1 flex items-center">
          <p className="font-medium">Profit</p>
        </div>
      </div>

      {productData.map((product, key) => (
        <div
          className="grid grid-cols-6 border-stroke border-t 2xl:px-7.5 dark:border-strokedark md:px-6 px-4 py-4.5 sm:grid-cols-8"
          key={key}
        >
          <div className="col-span-3 flex items-center">
            <div className="flex flex-col gap-4 sm:flex-row sm:items-center">
              <div className="h-12.5 rounded-md w-15">
                <img src={product.image} alt="Product" />
              </div>
              <p className="text-black text-sm dark:text-white">
                {product.name}
              </p>
            </div>
          </div>
          <div className="col-span-2 hidden items-center sm:flex">
            <p className="text-black text-sm dark:text-white">
              {product.category}
            </p>
          </div>
          <div className="col-span-1 flex items-center">
            <p className="text-black text-sm dark:text-white">
              ${product.price}
            </p>
          </div>
          <div className="col-span-1 flex items-center">
            <p className="text-black text-sm dark:text-white">{product.sold}</p>
          </div>
          <div className="col-span-1 flex items-center">
            <p className="text-meta-3 text-sm">${product.profit}</p>
          </div>
        </div>
      ))}
    </div>
  );
};

export default TableTwo;
